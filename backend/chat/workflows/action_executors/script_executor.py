
import subprocess

def execute_script(code: str) -> str:
    """
    更健壮的代码执行器，处理编码问题
    返回格式: "SUCCESS: <输出>" 或 "ERROR: <错误信息>"
    """
    try:
        # 创建一个新的进程配置
        process = subprocess.Popen(
            ["python", "-c", code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # 使用二进制模式读取，后续手动解码
            universal_newlines=False
        )

        # 设置超时并等待进程完成
        try:
            stdout, stderr = process.communicate(timeout=300)
        except subprocess.TimeoutExpired:
            process.kill()
            return "ERROR: 代码执行超时"

        # 尝试多种编码方式解码输出
        def try_decode(byte_data):
            for encoding in ['utf-8', 'gbk', 'latin1']:
                try:
                    return byte_data.decode(encoding)
                except UnicodeDecodeError:
                    continue
            return byte_data.decode('utf-8', errors='replace')  # 最终尝试替换非法字符

        # 解码输出
        stdout_decoded = try_decode(stdout) if stdout else ""
        stderr_decoded = try_decode(stderr) if stderr else ""

        # 返回结果
        if process.returncode == 0:
            return f"SUCCESS:\n{stdout_decoded.strip()}"
        else:
            return f"ERROR:\n{stderr_decoded.strip()}"

    except Exception as e:
        return f"EXCEPTION:\n{str(e)}"