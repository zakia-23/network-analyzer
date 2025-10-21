#!/usr/bin/env python3
"""
Multi-Host Network Quality Analyzer
Author: zakia-23
Description: Analyze multiple hosts with different packet sizes
"""

import subprocess
import re
import statistics
import time
from datetime import datetime

def ping_host(host, count=4, packet_size=56, timeout=10):
    """Execute ping command and return results"""
    try:
        cmd = ['ping', '-c', str(count), '-s', str(packet_size), '-W', str(timeout), host]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+5)
        
        if result.returncode == 0:
            return parse_ping_output(result.stdout, host, packet_size)
        else:
            return {"error": f"Ping failed - Host may be unreachable"}
            
    except subprocess.TimeoutExpired:
        return {"error": f"Ping timeout after {timeout} seconds"}
    except Exception as e:
        return {"error": f"Error: {str(e)}"}

def parse_ping_output(output, host, packet_size):
    """Parse ping command output"""
    lines = output.strip().split('\n')
    
    packets = []
    ip_address = host
    
    for line in lines:
        # Extract IP address from ping response
        if "PING" in line and "(" in line:
            ip_match = re.search(r'\((.*?)\)', line)
            if ip_match:
                ip_address = ip_match.group(1)
        
        # Extract ping times
        if "bytes from" in line and "time=" in line:
            match = re.search(r'time=([\d.]+) ms', line)
            if match:
                packets.append(float(match.group(1)))
    
    if packets:
        return {
            'host': host,
            'ip_address': ip_address,
            'packet_size': packet_size,
            'packets_sent': len(packets),
            'packet_loss': max(0, 4 - len(packets)),  # Estimate packet loss
            'times': packets,
            'avg_rtt': statistics.mean(packets),
            'min_rtt': min(packets),
            'max_rtt': max(packets),
            'jitter': statistics.stdev(packets) if len(packets) > 1 else 0,
            'status': 'SUCCESS'
        }
    else:
        return {"error": "No packets received", "status": "FAILED"}

def test_multiple_hosts(hosts, packet_sizes=[56, 128, 512]):
    """Test multiple hosts with different packet sizes"""
    print("🌐 MULTI-HOST NETWORK ANALYZER")
    print("=" * 60)
    
    all_results = []
    
    for host in hosts:
        print(f"\n🎯 Analyzing: {host}")
        print("=" * 40)
        
        host_results = []
        
        for size in packet_sizes:
            print(f"\n📦 Packet size: {size} bytes")
            print("-" * 25)
            
            result = ping_host(host, count=4, packet_size=size)
            
            if 'error' not in result:
                host_results.append(result)
                print_result(result)
            else:
                print(f"❌ {result['error']}")
            
            time.sleep(1)  # Wait between tests
        
        if host_results:
            all_results.append(host_results)
            print_host_summary(host_results)
    
    if all_results:
        print_comparison_summary(all_results)

def print_result(result):
    """Print single ping test result"""
    print(f"📍 IP: {result['ip_address']}")
    print(f"📊 Packets: {result['packets_sent']}/4 received")
    print(f"⏱️  RTT: Min={result['min_rtt']:.1f}ms, Avg={result['avg_rtt']:.1f}ms, Max={result['max_rtt']:.1f}ms")
    print(f"📈 Jitter: {result['jitter']:.2f}ms")
    print(f"🕒 Times: {', '.join([f'{t:.1f}ms' for t in result['times']])}")
    
    # Quality assessment
    quality = assess_quality(result)
    print(f"🎯 Quality: {quality}")

def assess_quality(result):
    """Assess network quality based on metrics"""
    if result['packet_loss'] > 2:
        return "🔴 POOR (High packet loss)"
    elif result['avg_rtt'] > 200:
        return "🔴 POOR (Very high latency)"
    elif result['avg_rtt'] > 100:
        return "🟡 FAIR (High latency)"
    elif result['jitter'] > 30:
        return "🟡 FAIR (High jitter)"
    elif result['avg_rtt'] < 30 and result['jitter'] < 10:
        return "🟢 EXCELLENT"
    else:
        return "🟢 GOOD"

def print_host_summary(host_results):
    """Print summary for a single host"""
    avg_rtts = [r['avg_rtt'] for r in host_results]
    best_size = min(host_results, key=lambda x: x['avg_rtt'])
    worst_size = max(host_results, key=lambda x: x['avg_rtt'])
    
    print(f"\n📋 HOST SUMMARY: {host_results[0]['host']}")
    print(f"📍 IP Address: {host_results[0]['ip_address']}")
    print(f"📊 Best performance: {best_size['packet_size']} bytes ({best_size['avg_rtt']:.1f}ms)")
    print(f"📊 Worst performance: {worst_size['packet_size']} bytes ({worst_size['avg_rtt']:.1f}ms)")
    print(f"📈 Average RTT across all tests: {statistics.mean(avg_rtts):.1f}ms")

def print_comparison_summary(all_results):
    """Print comparison between all tested hosts"""
    print("\n" + "=" * 60)
    print("📊 COMPARISON SUMMARY - ALL HOSTS")
    print("=" * 60)
    
    host_stats = []
    
    for host_result in all_results:
        host = host_result[0]['host']
        ip = host_result[0]['ip_address']
        avg_rtts = [r['avg_rtt'] for r in host_result]
        overall_avg = statistics.mean(avg_rtts)
        
        host_stats.append({
            'host': host,
            'ip': ip,
            'avg_rtt': overall_avg,
            'best_rtt': min([r['avg_rtt'] for r in host_result]),
            'status': 'ONLINE'
        })
    
    # Sort by best average RTT
    host_stats.sort(key=lambda x: x['avg_rtt'])
    
    print("\n🏆 RANKING (Best to Worst):")
    for i, stats in enumerate(host_stats, 1):
        print(f"{i}. {stats['host']} ({stats['ip']}) - {stats['avg_rtt']:.1f}ms avg")
    
    print(f"\n✅ Fastest: {host_stats[0]['host']} ({host_stats[0]['best_rtt']:.1f}ms)")
    print(f"⏱️  Slowest: {host_stats[-1]['host']} ({host_stats[-1]['avg_rtt']:.1f}ms)")

def main():
    """Main function with interactive host selection"""
    
    # Predefined list of popular hosts to test
    popular_hosts = [
        "google.com",
        "github.com",
        "stackoverflow.com",
        "wikipedia.org",
        "youtube.com",
        "facebook.com",
        "amazon.com",
        "microsoft.com",
        "cisco.com",
        "8.8.8.8"  # Google DNS
    ]
    
    print("🌐 MULTI-HOST NETWORK ANALYZER")
    print("=" * 50)
    print("\nChoose hosts to analyze:")
    print("1. Test popular websites (predefined list)")
    print("2. Enter custom hosts")
    print("3. Quick test (google.com, github.com, cisco.com)")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == '1':
        print("\n📋 Popular hosts available:")
        for i, host in enumerate(popular_hosts, 1):
            print(f"  {i}. {host}")
        
        print("  a. Test ALL hosts")
        selection = input("\nEnter numbers (e.g., 1,3,5) or 'a' for all: ").strip()
        
        if selection.lower() == 'a':
            hosts_to_test = popular_hosts
        else:
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                hosts_to_test = [popular_hosts[i] for i in indices if 0 <= i < len(popular_hosts)]
            except:
                print("❌ Invalid selection, using default hosts")
                hosts_to_test = ["google.com", "github.com", "cisco.com"]
    
    elif choice == '2':
        custom_hosts = input("\nEnter hosts (comma-separated): ").strip()
        hosts_to_test = [host.strip() for host in custom_hosts.split(',') if host.strip()]
    
    elif choice == '3':
        hosts_to_test = ["google.com", "github.com", "cisco.com"]
    
    else:
        print("❌ Invalid choice, using default hosts")
        hosts_to_test = ["google.com", "github.com", "cisco.com"]
    
    if not hosts_to_test:
        hosts_to_test = ["google.com", "github.com", "cisco.com"]
    
    print(f"\n🎯 Selected hosts: {', '.join(hosts_to_test)}")
    
    # Packet sizes to test
    packet_sizes = [32, 56, 128, 512]
    
    test_multiple_hosts(hosts_to_test, packet_sizes)

if __name__ == "__main__":
    main()
