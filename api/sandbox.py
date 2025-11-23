import subprocess, tempfile, textwrap

def run_python(code: str, timeout=5):
    code = textwrap.dedent(code)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code)
        path = f.name
    try:
        res = subprocess.run(
            ["python", path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {"stdout": res.stdout, "stderr": res.stderr, "returncode": res.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "TimeoutExpired", "returncode": 124}
