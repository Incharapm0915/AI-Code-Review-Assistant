import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Dict, Optional

MAX_OUTPUT_CHARS = 20000
EXEC_TIMEOUT_SECONDS = 10


def _truncate(text: str) -> str:
    if text and len(text) > MAX_OUTPUT_CHARS:
        return text[:MAX_OUTPUT_CHARS] + f'\n…[output truncated at {MAX_OUTPUT_CHARS} characters]'
    return text or ''


def _run_subprocess(cmd, cwd, stdin_data, timeout=EXEC_TIMEOUT_SECONDS) -> Dict:
    start = time.time()
    try:
        proc = subprocess.run(
            cmd, cwd=cwd, input=stdin_data, capture_output=True, text=True, timeout=timeout,
        )
        return {
            'stdout': _truncate(proc.stdout),
            'stderr': _truncate(proc.stderr),
            'exit_code': proc.returncode,
            'timed_out': False,
            'duration_ms': int((time.time() - start) * 1000),
        }
    except subprocess.TimeoutExpired as e:
        return {
            'stdout': _truncate(e.stdout or ''),
            'stderr': _truncate((e.stderr or '') + f'\n[Execution timed out after {timeout}s]'),
            'exit_code': None,
            'timed_out': True,
            'duration_ms': timeout * 1000,
        }


class CodeRunner:
    """Executes user-submitted code outside the request process.

    Safety measures applied here: a fresh throwaway temp directory per run
    (deleted afterwards), a hard wall-clock timeout that kills runaway
    processes, truncated output, and Python's `-I` isolated mode. There is
    NO OS-level sandbox (no container, no network/filesystem jail) — code
    runs with the same privileges as the Flask process. This is acceptable
    for a trusted, single-user local/dev tool; it is NOT safe to expose to
    untrusted users without adding real isolation (e.g. Docker/gVisor) first.
    """

    LANGUAGES = {'python', 'javascript', 'java', 'cpp'}

    def run(self, code: str, language: str, stdin: str = '') -> Dict:
        if language not in self.LANGUAGES:
            return {'success': False, 'error': f'Running {language} code is not supported.'}

        workdir = tempfile.mkdtemp(prefix='ai_review_run_')
        try:
            method = getattr(self, f'_run_{language}')
            result = method(code, workdir, stdin)
            if result is None:
                return {'success': False, 'error': self._missing_runtime_message(language)}
            result['success'] = True
            return result
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    @staticmethod
    def _missing_runtime_message(language: str) -> str:
        names = {
            'python': 'Python interpreter',
            'javascript': 'Node.js (node)',
            'java': 'a JDK (javac/java)',
            'cpp': 'a C++ compiler (g++ or MSVC cl)',
        }
        return (f'{names.get(language, language)} is not installed on this server, '
                f'so the code cannot be run. Static analysis above still applies.')

    def _run_python(self, code: str, workdir: str, stdin: str) -> Optional[Dict]:
        path = os.path.join(workdir, 'main.py')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(code)
        # -I: isolated mode — ignores PYTHONPATH/PYTHONHOME and user site-packages,
        # and does not implicitly trust the script's own directory on sys.path.
        return _run_subprocess([sys.executable, '-I', 'main.py'], workdir, stdin)

    def _run_javascript(self, code: str, workdir: str, stdin: str) -> Optional[Dict]:
        if shutil.which('node') is None:
            return None
        path = os.path.join(workdir, 'main.js')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(code)
        return _run_subprocess(['node', 'main.js'], workdir, stdin)

    def _run_java(self, code: str, workdir: str, stdin: str) -> Optional[Dict]:
        if shutil.which('javac') is None or shutil.which('java') is None:
            return None

        match = re.search(r'public\s+class\s+(\w+)', code) or re.search(r'\bclass\s+(\w+)', code)
        class_name = match.group(1) if match else 'Main'

        path = os.path.join(workdir, f'{class_name}.java')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(code)

        compile_result = _run_subprocess(['javac', f'{class_name}.java'], workdir, '')
        if compile_result['exit_code'] != 0:
            compile_result['stage'] = 'compile'
            return compile_result

        run_result = _run_subprocess(['java', '-cp', workdir, class_name], workdir, stdin)
        run_result['stage'] = 'run'
        return run_result

    def _run_cpp(self, code: str, workdir: str, stdin: str) -> Optional[Dict]:
        compiler = 'g++' if shutil.which('g++') else ('cl' if shutil.which('cl') else None)
        if compiler is None:
            return None

        path = os.path.join(workdir, 'main.cpp')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(code)
        exe_path = os.path.join(workdir, 'main.exe' if os.name == 'nt' else 'main')

        if compiler == 'g++':
            compile_cmd = ['g++', 'main.cpp', '-O0', '-o', exe_path]
        else:
            compile_cmd = ['cl', '/nologo', 'main.cpp', f'/Fe:{exe_path}']

        compile_result = _run_subprocess(compile_cmd, workdir, '')
        if compile_result['exit_code'] != 0:
            compile_result['stage'] = 'compile'
            return compile_result

        run_result = _run_subprocess([exe_path], workdir, stdin)
        run_result['stage'] = 'run'
        return run_result
