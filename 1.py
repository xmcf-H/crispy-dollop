#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
域名绑定验证脚本
功能：读取域名列表，验证绑定固定host前后的页面变化
用法：python host_verifier.py
"""

import requests
import hashlib
import difflib
import os
import re
import time
from datetime import datetime
import sys
from urllib.parse import urlparse

def read_domain_list(filename='1.txt'):
    """读取域名列表文件，格式：IP 域名"""
    bindings = []
    if not os.path.exists(filename):
        print(f"错误：文件 {filename} 不存在")
        print("请创建 1.txt 文件，每行格式为：IP 域名")
        print("例如：172.20.5.129 www.baidu.com")
        return None
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            parts = line.split()
            if len(parts) != 2:
                print(f"警告：第{line_num}行格式错误，跳过: {line}")
                continue
                
            ip, domain = parts
            bindings.append((ip, domain))
    
    if not bindings:
        print("错误：没有找到有效的域名绑定配置")
        return None
    
    print(f"成功读取 {len(bindings)} 个域名绑定配置")
    return bindings

def get_page_content(url, timeout=10, use_hosts=False, custom_ip=None, custom_domain=None):
    """获取网页内容"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }
    
    session = requests.Session()
    
    if use_hosts and custom_ip and custom_domain:
        # 通过修改Hosts文件的方式访问
        # 这里我们通过修改请求头来模拟Hosts效果
        # 注意：这不会真正修改系统hosts文件，只是模拟测试
        url_parsed = urlparse(url)
        url_with_ip = url.replace(url_parsed.netloc, custom_ip)
        
        # 在请求头中添加原始域名
        headers['Host'] = custom_domain
        
        try:
            response = session.get(url_with_ip, headers=headers, timeout=timeout, verify=False, allow_redirects=True)
        except requests.exceptions.RequestException as e:
            print(f"  模拟hosts访问失败: {e}")
            return None
    else:
        # 正常访问
        try:
            response = session.get(url, headers=headers, timeout=timeout, verify=False, allow_redirects=True)
        except requests.exceptions.RequestException as e:
            print(f"  正常访问失败: {e}")
            return None
    
    if response.status_code != 200:
        print(f"  HTTP状态码: {response.status_code}")
        return None
    
    return response.text

def extract_page_info(content):
    """提取页面的关键信息"""
    info = {
        'title': '未找到标题',
        'charset': 'utf-8',
        'content_length': len(content) if content else 0,
        'hash': None
    }
    
    if not content:
        return info
    
    # 计算内容哈希
    info['hash'] = hashlib.md5(content.encode('utf-8', errors='ignore')).hexdigest()[:16]
    
    # 提取标题
    title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
    if title_match:
        info['title'] = title_match.group(1).strip()[:100]
    
    # 尝试检测字符集
    charset_match = re.search(r'charset=["\']?([a-zA-Z0-9-]+)["\']?', content, re.IGNORECASE)
    if charset_match:
        info['charset'] = charset_match.group(1).lower()
    
    return info

def compare_contents(content1, content2, name1="正常访问", name2="Hosts绑定访问"):
    """比较两个内容的差异"""
    if content1 is None or content2 is None:
        return "无法比较，至少有一个内容为空"
    
    if content1 == content2:
        return "内容完全相同"
    
    # 使用difflib比较差异
    diff = difflib.unified_diff(
        content1.splitlines(keepends=True),
        content2.splitlines(keepends=True),
        fromfile=name1,
        tofile=name2,
        n=3
    )
    
    diff_text = ''.join(diff)
    
    if diff_text:
        # 统计差异行数
        diff_lines = diff_text.count('\n')
        return f"内容有差异 ({diff_lines} 行不同)"
    else:
        return "内容相同"

def save_results(results, output_dir='results'):
    """保存测试结果"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'host_verification_{timestamp}.txt')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("域名绑定验证结果\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        for ip, domain, result in results:
            f.write(f"域名: {domain}\n")
            f.write(f"绑定IP: {ip}\n")
            f.write(f"正常访问URL: http://{domain}\n")
            f.write(f"模拟Hosts访问URL: http://{ip} (Host: {domain})\n")
            f.write(f"测试结果: {result['status']}\n")
            
            if 'before' in result and 'after' in result:
                f.write("\n[正常访问]\n")
                f.write(f"  标题: {result['before']['title']}\n")
                f.write(f"  内容长度: {result['before']['content_length']} 字符\n")
                f.write(f"  内容哈希: {result['before']['hash']}\n")
                
                f.write("\n[Hosts绑定访问]\n")
                f.write(f"  标题: {result['after']['title']}\n")
                f.write(f"  内容长度: {result['after']['content_length']} 字符\n")
                f.write(f"  内容哈希: {result['after']['hash']}\n")
                
                f.write(f"\n对比结果: {result['comparison']}\n")
            
            f.write("-" * 80 + "\n\n")
    
    print(f"\n详细结果已保存到: {output_file}")
    return output_file

def generate_hosts_file(bindings, output_dir='results'):
    """生成需要添加到hosts文件的内容"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    hosts_file = os.path.join(output_dir, f'hosts_entries_{timestamp}.txt')
    
    with open(hosts_file, 'w', encoding='utf-8') as f:
        f.write("# 以下内容可以添加到系统hosts文件中\n")
        f.write("# 位置: Windows: C:\\Windows\\System32\\drivers\\etc\\hosts\n")
        f.write("#        Mac/Linux: /etc/hosts\n")
        f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for ip, domain in bindings:
            f.write(f"{ip}  {domain}\n")
    
    print(f"Hosts配置已保存到: {hosts_file}")
    return hosts_file

def main():
    print("域名绑定验证工具")
    print("=" * 50)
    
    # 读取域名列表
    bindings = read_domain_list('1.txt')
    if not bindings:
        return
    
    print("\n开始测试...")
    print("-" * 50)
    
    results = []
    
    for i, (ip, domain) in enumerate(bindings, 1):
        print(f"\n[{i}/{len(bindings)}] 测试域名: {domain} -> {ip}")
        
        # 正常访问
        print(f"  1. 正常访问 {domain}...")
        normal_url = f"http://{domain}"
        normal_content = get_page_content(normal_url, use_hosts=False)
        normal_info = extract_page_info(normal_content)
        
        if normal_content is None:
            print(f"  × 正常访问失败")
            normal_info = {'title': '访问失败', 'content_length': 0, 'hash': 'N/A'}
        
        # 等待一下，避免请求过快
        time.sleep(1)
        
        # 模拟Hosts绑定访问
        print(f"  2. 模拟Hosts绑定访问 ({ip} -> {domain})...")
        hosts_content = get_page_content(f"http://{ip}", use_hosts=True, custom_ip=ip, custom_domain=domain)
        hosts_info = extract_page_info(hosts_content)
        
        if hosts_content is None:
            print(f"  × Hosts绑定访问失败")
            hosts_info = {'title': '访问失败', 'content_length': 0, 'hash': 'N/A'}
        
        # 比较结果
        if normal_content and hosts_content:
            comparison = compare_contents(normal_content, hosts_content)
        else:
            comparison = "无法比较（至少一次访问失败）"
        
        # 判断是否相同
        if normal_info.get('hash') and hosts_info.get('hash'):
            if normal_info['hash'] == hosts_info['hash']:
                status = "✓ 内容相同 (hash一致)"
            else:
                status = "⚠ 内容不同 (hash不一致)"
        else:
            status = "? 访问失败，无法比较"
        
        result = {
            'status': status,
            'comparison': comparison,
            'before': normal_info,
            'after': hosts_info
        }
        
        print(f"  结果: {status}")
        print(f"  对比: {comparison}")
        
        results.append((ip, domain, result))
    
    # 生成结果报告
    print("\n" + "=" * 50)
    print("测试完成，生成报告...")
    
    # 保存详细结果
    result_file = save_results(results)
    
    # 生成hosts配置
    hosts_file = generate_hosts_file(bindings)
    
    # 统计结果
    same_count = sum(1 for _, _, r in results if "内容相同" in r['status'])
    diff_count = sum(1 for _, _, r in results if "内容不同" in r['status'])
    fail_count = sum(1 for _, _, r in results if "访问失败" in r['status'])
    
    print("\n" + "=" * 50)
    print("测试统计:")
    print(f"  总计测试: {len(bindings)} 个域名")
    print(f"  内容相同: {same_count} 个")
    print(f"  内容不同: {diff_count} 个")
    print(f"  访问失败: {fail_count} 个")
    print(f"\n详细结果: {result_file}")
    print(f"Hosts配置: {hosts_file}")
    
    # 使用说明
    print("\n" + "=" * 50)
    print("使用说明:")
    print("1. 如果内容相同，说明绑定hosts后访问的网站与原来相同")
    print("2. 如果内容不同，说明绑定hosts后访问到了不同的服务器")
    print("3. 如果访问失败，可能是IP地址无效或服务器配置问题")
    print("\n要实际应用hosts绑定，请:")
    print("1. 以管理员身份编辑系统hosts文件")
    print("2. 将生成的hosts_entries_*.txt文件内容复制到hosts文件中")
    print("3. 保存文件并刷新DNS缓存（执行: ipconfig /flushdns 或在终端执行对应命令）")

if __name__ == "__main__":
    # 禁用SSL警告
    requests.packages.urllib3.disable_warnings()
    
    # 创建示例配置文件
    if not os.path.exists('1.txt'):
        with open('1.txt', 'w', encoding='utf-8') as f:
            f.write("# 域名绑定配置文件\n")
            f.write("# 格式: IP地址 域名\n")
            f.write("# 例如:\n")
            f.write("172.20.5.129 www.baidu.com\n")
            f.write("8.8.8.8 www.google.com\n")
            f.write("192.168.1.1 www.example.com\n")
        print("已创建示例配置文件 1.txt")
        print("请编辑此文件，添加您要测试的域名绑定")
        input("按Enter键开始测试...")
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序被用户中断")
    except Exception as e:
        print(f"\n程序出错: {e}")
        import traceback
        traceback.print_exc()