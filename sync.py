import os
import subprocess
import sys
import hashlib
import time

REPO_PATH = os.path.dirname(os.path.abspath(__file__))
REMOTE_URL = "https://github.com/ZJH0601/H_S.git"

def run_command(cmd, cwd=None):
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or REPO_PATH,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return "", e.stderr.strip()

def get_git_status():
    stdout, stderr = run_command(["git", "status", "--porcelain"])
    if stderr:
        return None, stderr
    return stdout, None

def get_file_hash(filepath):
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception:
        return None

def check_for_changes():
    stdout, stderr = run_command(["git", "diff", "--name-only"])
    if stderr:
        return None, stderr
    
    modified_files = stdout.strip().split("\n") if stdout else []
    return modified_files, None

def sync_to_github():
    print("=" * 60)
    print("开始同步到 GitHub...")
    print("=" * 60)
    
    print("\n[1/5] 检查 Git 状态...")
    status, err = get_git_status()
    if err:
        print(f"❌ 错误: {err}")
        return False
    
    if not status:
        print("✅ 没有需要同步的更改")
        return True
    
    print(f"📋 检测到以下文件有更改:")
    for line in status.strip().split("\n"):
        print(f"   {line}")
    
    print("\n[2/5] 添加所有更改...")
    stdout, err = run_command(["git", "add", "."])
    if err:
        print(f"❌ 错误: {err}")
        return False
    print("✅ 已添加")
    
    print("\n[3/5] 提交更改...")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    stdout, err = run_command(["git", "commit", "-m", f"自动同步: {timestamp}"])
    if err:
        print(f"❌ 错误: {err}")
        return False
    print(f"✅ 提交成功: {stdout}")
    
    print("\n[4/5] 推送到 GitHub...")
    stdout, err = run_command(["git", "push", "origin", "master"])
    if err:
        print(f"❌ 推送失败: {err}")
        print("🔄 尝试重新推送...")
        time.sleep(2)
        stdout, err = run_command(["git", "push", "origin", "master"])
        if err:
            print(f"❌ 重新推送仍失败: {err}")
            return False
    print(f"✅ 推送成功")
    
    print("\n[5/5] 验证同步结果...")
    stdout, err = run_command(["git", "log", "--oneline", "-1"])
    if err:
        print(f"⚠️ 验证失败: {err}")
    else:
        print(f"✅ 当前最新提交: {stdout}")
    
    print("\n" + "=" * 60)
    print("🎉 同步完成!")
    print(f"🌐 网站地址: https://zjh0601.github.io/H_S/")
    print("⏳ GitHub Pages 部署可能需要 1-3 分钟")
    print("=" * 60)
    
    return True

def check_remote_status():
    print("\n检查远程仓库状态...")
    stdout, err = run_command(["git", "remote", "-v"])
    if err:
        print(f"❌ 错误: {err}")
        return
    
    print("远程仓库配置:")
    for line in stdout.strip().split("\n"):
        print(f"   {line}")
    
    stdout, err = run_command(["git", "fetch", "origin"])
    if err:
        print(f"❌ 获取远程分支失败: {err}")
        return
    
    stdout, err = run_command(["git", "log", "--oneline", "origin/master..master"])
    if err:
        print(f"❌ 比较分支失败: {err}")
        return
    
    if stdout:
        count = len(stdout.strip().split('\n'))
        print(f"本地有 {count} 个提交需要推送")
    else:
        print("本地与远程同步")

    stdout, err = run_command(["git", "log", "--oneline", "master..origin/master"])
    if err:
        print(f"比较分支失败: {err}")
        return
    
    if stdout:
        count = len(stdout.strip().split('\n'))
        print(f"远程有 {count} 个提交需要拉取")
    else:
        print("远程没有新提交")

def main():
    os.chdir(REPO_PATH)
    
    if not os.path.exists(os.path.join(REPO_PATH, ".git")):
        print("错误: 当前目录不是 Git 仓库")
        print("请先初始化 Git 仓库:")
        print("   git init")
        print("   git remote add origin https://github.com/ZJH0601/H_S.git")
        sys.exit(1)
    
    if len(sys.argv) < 2:
        print("欢迎使用绘摄网站同步工具")
        print("-" * 40)
        print("用法:")
        print("   python sync.py status    # 检查本地与远程状态")
        print("   python sync.py sync      # 同步到 GitHub")
        print("   python sync.py auto      # 自动检查并同步")
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command == "status":
        check_remote_status()
    elif command == "sync":
        success = sync_to_github()
        if not success:
            print("\n同步失败，请检查网络连接或 Git 配置")
            sys.exit(1)
    elif command == "auto":
        check_remote_status()
        modified, err = check_for_changes()
        if err:
            print(f"检查更改失败: {err}")
            sys.exit(1)
        if modified:
            print(f"\n检测到 {len(modified)} 个文件有更改，开始同步...")
            success = sync_to_github()
            if not success:
                print("\n同步失败")
                sys.exit(1)
        else:
            print("\n没有需要同步的更改")
    else:
        print(f"未知命令: {command}")
        print("可用命令: status, sync, auto")
        sys.exit(1)

if __name__ == "__main__":
    main()