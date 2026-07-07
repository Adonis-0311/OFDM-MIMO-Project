"""torchless_load.py -- load a torch .pt zip checkpoint without torch (numpy out)."""
import zipfile, pickle, io
import numpy as np

DTYPES = {
    'FloatStorage': np.float32, 'DoubleStorage': np.float64,
    'LongStorage': np.int64, 'IntStorage': np.int32,
    'HalfStorage': np.float16, 'BoolStorage': np.bool_,
    'ByteStorage': np.uint8, 'CharStorage': np.int8,
}

def load_pt(path):
    zf = zipfile.ZipFile(path)
    prefix = zf.namelist()[0].split('/')[0]

    def rebuild_tensor_v2(storage, storage_offset, size, stride, *args):
        key, dtype = storage
        arr = np.frombuffer(zf.read(f'{prefix}/data/{key}'), dtype=dtype)
        if size:
            return np.lib.stride_tricks.as_strided(
                arr[storage_offset:], shape=tuple(size),
                strides=tuple(s * arr.itemsize for s in stride)).copy()
        return arr[storage_offset:storage_offset + 1].copy().reshape(())

    class U(pickle.Unpickler):
        def find_class(self, module, name):
            if name == '_rebuild_tensor_v2':
                return rebuild_tensor_v2
            if name.endswith('Storage') and module.startswith('torch'):
                return name                      # marker: plain string
            if module.startswith('torch'):
                return lambda *a, **k: None
            if module == 'collections' and name == 'OrderedDict':
                from collections import OrderedDict
                return OrderedDict
            if module.startswith('numpy'):
                import importlib
                return getattr(importlib.import_module(module), name)
            raise pickle.UnpicklingError(f'blocked {module}.{name}')
        def persistent_load(self, pid):
            # ('storage', <storage type marker str>, key, location, numel)
            name = pid[1] if isinstance(pid[1], str) else 'FloatStorage'
            return (pid[2], DTYPES.get(name, np.float32))

    return U(io.BytesIO(zf.read(f'{prefix}/data.pkl'))).load()
