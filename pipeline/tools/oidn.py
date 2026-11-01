"""Intel Open Image Denoise through ctypes, using the library that ships inside the bpy wheel.
Used to denoise baked lightmaps (Cycles does not denoise bakes), so a group can bake at lower SPP.

    from oidn import denoise_rgb;  out = denoise_rgb(rgb_float32_HxWx3, hdr=True)
"""
import ctypes, glob, os
import numpy as np

_lib = None


def _load():
    global _lib
    if _lib:
        return _lib
    import bpy
    cands = []
    for root in {os.path.dirname(os.path.dirname(bpy.__file__)), "/usr/local/lib/python3.13/dist-packages/bpy"}:
        cands += glob.glob(os.path.join(root, "**", "libOpenImageDenoise.so*"), recursive=True)
    if not cands:
        raise RuntimeError("libOpenImageDenoise not found next to bpy")
    _lib = ctypes.CDLL(sorted(cands, key=len)[0])
    L = _lib
    L.oidnNewDevice.restype = ctypes.c_void_p; L.oidnNewDevice.argtypes = [ctypes.c_int]
    L.oidnCommitDevice.argtypes = [ctypes.c_void_p]
    L.oidnNewFilter.restype = ctypes.c_void_p; L.oidnNewFilter.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
    L.oidnSetSharedFilterImage.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_int,
                                           ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t]
    L.oidnSetFilterBool.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_bool]
    L.oidnCommitFilter.argtypes = [ctypes.c_void_p]; L.oidnExecuteFilter.argtypes = [ctypes.c_void_p]
    L.oidnGetDeviceError.restype = ctypes.c_int; L.oidnGetDeviceError.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_char_p)]
    L.oidnReleaseFilter.argtypes = [ctypes.c_void_p]; L.oidnReleaseDevice.argtypes = [ctypes.c_void_p]
    return L


def denoise_rgb(rgb, hdr=True, albedo=None):
    L = _load()
    h, w, _ = rgb.shape
    src = np.ascontiguousarray(rgb, dtype=np.float32); dst = np.empty_like(src)
    alb = np.ascontiguousarray(np.clip(albedo, 0, 1), dtype=np.float32) if albedo is not None else None
    dev = L.oidnNewDevice(1)                      # OIDN_DEVICE_TYPE_CPU
    L.oidnCommitDevice(dev)
    f = L.oidnNewFilter(dev, b"RT")
    FLOAT3 = 3
    L.oidnSetSharedFilterImage(f, b"color", src.ctypes.data, FLOAT3, w, h, 0, 0, 0)
    L.oidnSetSharedFilterImage(f, b"output", dst.ctypes.data, FLOAT3, w, h, 0, 0, 0)
    if alb is not None:                           # texture detail guide: keeps labels/text/grain sharp
        L.oidnSetSharedFilterImage(f, b"albedo", alb.ctypes.data, FLOAT3, w, h, 0, 0, 0)
    L.oidnSetFilterBool(f, b"hdr", hdr)
    L.oidnCommitFilter(f); L.oidnExecuteFilter(f)
    msg = ctypes.c_char_p()
    err = L.oidnGetDeviceError(dev, ctypes.byref(msg))
    L.oidnReleaseFilter(f); L.oidnReleaseDevice(dev)
    if err:
        raise RuntimeError(f"OIDN error {err}: {msg.value}")
    return dst


def _px(img):
    w, h = img.size
    a = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(a)
    return a.reshape(h, w, 4)


def denoise_image(img, albedo_img=None):
    """In-place denoise of a bpy float image (RGBA), optionally guided by a baked albedo image."""
    a = _px(img)
    alb = _px(albedo_img)[:, :, :3] if albedo_img is not None else None
    a[:, :, :3] = denoise_rgb(a[:, :, :3], albedo=alb)
    img.pixels.foreach_set(a.ravel())
    img.update()
