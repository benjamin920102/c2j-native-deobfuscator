"""Verify setup outputs and ZIP the full checkout, excluding only Git metadata.

Run from the repository root after setup. Output lives outside the checkout.
Symlinks and Unix permissions are retained in the ZIP.
"""
import os
from pathlib import Path
import stat
import struct
import subprocess
import zipfile


def main():
    root = Path(__file__).resolve().parents[1]
    platform = os.environ['PACKAGE_PLATFORM']
    agent = root / 'native/build/lib' / os.environ['PACKAGE_AGENT']
    arch = os.environ['J2C_ARCH']
    data = agent.read_bytes()
    if platform.startswith('windows-'):
        assert data[:2] == b'MZ', 'Agent is not a Windows PE file'
        pe = struct.unpack_from('<I', data, 0x3C)[0]
        assert data[pe:pe + 4] == b'PE\0\0', 'Invalid PE header'
        machine = struct.unpack_from('<H', data, pe + 4)[0]
        assert machine == {'x64': 0x8664, 'arm64': 0xAA64}[arch], 'Wrong DLL architecture'
        python = root / 'py/.venv/Scripts/python.exe'
    else:
        assert data[:5] == b'\x7fELF\x02', 'Agent is not a 64-bit ELF file'
        machine = struct.unpack_from('<H' if data[5] == 1 else '>H', data, 18)[0]
        assert machine == {'x64': 62, 'arm64': 183}[arch], 'Wrong SO architecture'
        python = root / 'py/.venv/bin/python'
    assert python.is_file(), 'Setup did not create the Python environment'
    # Importing the bindings and disassembling real instructions also loads the
    # native libraries, catching missing DLLs and wrong-architecture builds.
    subprocess.run([
        str(python), '-c',
        'import capstone, lief; '
        'x86 = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64); '
        'arm = capstone.Cs(capstone.CS_ARCH_ARM64, capstone.CS_MODE_ARM); '
        'assert next(x86.disasm(bytes.fromhex("90"), 0)).mnemonic == "nop"; '
        'assert next(arm.disasm(bytes.fromhex("1f2003d5"), 0)).mnemonic == "nop"; '
        'print("Native dependencies OK: Capstone", capstone.__version__, '
        '"/ LIEF", lief.__version__)',
    ], check=True, cwd=root)
    for module in ('jar-parser', 'class-rebuilder', 'trace-to-bytecode', 'desktop-ui'):
        assert (root / f'jvm/{module}/build/install/{module}/lib').is_dir(), f'Missing JVM distribution: {module}'
    output = Path(os.environ['RUNNER_TEMP']) / 'c2j-packages'
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f'c2j-native-deobfuscator-{platform}.zip'
    prefix = f'c2j-native-deobfuscator-{platform}'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for directory, dirs, files in os.walk(root, followlinks=False):
            base = Path(directory)
            if base == root:
                dirs[:] = [d for d in dirs if d != '.git']
                files = [f for f in files if f != '.git']
            for name in sorted(dirs + files):
                path = base / name
                dest = f'{prefix}/{path.relative_to(root).as_posix()}'
                if path.is_symlink():
                    info = zipfile.ZipInfo(dest)
                    info.create_system = 3
                    info.external_attr = (stat.S_IFLNK | 0o777) << 16
                    z.writestr(info, os.readlink(path))
                else:
                    z.write(path, dest)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None, 'ZIP integrity check failed'
    print(f'Created {archive} ({archive.stat().st_size:,} bytes)')


if __name__ == '__main__':
    main()
