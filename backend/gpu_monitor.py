"""
GPU显存监测模块
使用pynvml库获取GPU显存使用率和相关信息
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional

try:
    import pynvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False
    print("警告: pynvml库未安装，GPU监测功能将不可用")
    print("请运行: pip install pynvml")

class GPUMonitor:
    """GPU显存监测器"""
    
    def __init__(self):
        self.initialized = False
        self.device_count = 0
        self.devices = []
        
        if NVML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.initialized = True
                self.device_count = pynvml.nvmlDeviceGetCount()
                print(f"GPU显存监测器初始化成功，检测到 {self.device_count} 个GPU设备")
                
                # 初始化设备列表
                for i in range(self.device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle)
                    self.devices.append({
                        'index': i,
                        'handle': handle,
                        'name': name
                    })
                    print(f"GPU {i}: {name}")
                    
            except Exception as e:
                print(f"GPU显存监测器初始化失败: {e}")
                self.initialized = False
    
    def get_gpu_info(self, device_index: int = 0) -> Dict[str, Any]:
        """获取指定GPU的显存信息"""
        if not self.initialized or device_index >= self.device_count:
            return {
                'available': False,
                'error': 'GPU不可用或设备索引超出范围'
            }
        
        try:
            device = self.devices[device_index]
            handle = device['handle']
            
            # 获取显存信息
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            memory_used = int(memory_info.used)
            memory_total = int(memory_info.total)
            memory_free = int(memory_info.free)
            memory_usage = (memory_used / memory_total) * 100 if memory_total > 0 else 0
            

            
            # 获取GPU使用率（作为参考）
            try:
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_usage = utilization.gpu
            except:
                gpu_usage = 0
            
            # 获取温度
            try:
                temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            except:
                temperature = 0
            
            # 获取风扇转速
            try:
                fan_speed = pynvml.nvmlDeviceGetFanSpeed(handle)
            except:
                fan_speed = 0
            
            # 获取功率信息
            try:
                power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # 转换为瓦特
                power_limit = pynvml.nvmlDeviceGetEnforcedPowerLimit(handle) / 1000.0
            except:
                power_usage = 0
                power_limit = 0
            
            return {
                'available': True,
                'device_index': device_index,
                'device_name': device['name'],
                'memory_usage': round(memory_usage, 1),
                'memory_used_mb': round(memory_used / 1024 / 1024, 1),
                'memory_free_mb': round(memory_free / 1024 / 1024, 1),
                'memory_total_mb': round(memory_total / 1024 / 1024, 1),
                'memory_used_gb': round(memory_used / 1024 / 1024 / 1024, 2),
                'memory_free_gb': round(memory_free / 1024 / 1024 / 1024, 2),
                'memory_total_gb': round(memory_total / 1024 / 1024 / 1024, 2),
                'gpu_usage': gpu_usage,  # 作为参考信息
                'temperature': temperature,
                'fan_speed': fan_speed,
                'power_usage_w': round(power_usage, 1),
                'power_limit_w': round(power_limit, 1),
                'percentage_full': memory_usage / 100.0,  # 前端期望的格式，基于显存使用率（0-1之间的小数）
                'gpu_model': device['name']
            }
            
        except Exception as e:
            return {
                'available': False,
                'error': f'获取GPU显存信息失败: {str(e)}'
            }
    
    def get_all_gpus_info(self) -> Dict[str, Any]:
        """获取所有GPU的显存信息"""
        if not self.initialized:
            return {
                'available': False,
                'error': 'GPU显存监测器未初始化'
            }
        
        gpus_info = []
        for i in range(self.device_count):
            gpu_info = self.get_gpu_info(i)
            if gpu_info['available']:
                gpus_info.append(gpu_info)
        
        return {
            'available': True,
            'device_count': self.device_count,
            'gpus': gpus_info
        }
    
    def cleanup(self):
        """清理资源"""
        if self.initialized and NVML_AVAILABLE:
            try:
                pynvml.nvmlShutdown()
                print("GPU显存监测器已关闭")
            except:
                pass

# 全局GPU监测器实例
gpu_monitor = GPUMonitor()

async def start_gpu_monitoring(websocket, user_session: dict, interval: float = 2.0):
    """启动GPU显存监测任务"""
    if not gpu_monitor.initialized:
        print("GPU显存监测不可用，跳过监测任务")
        return
    
    try:
        while True:
            # 获取GPU显存信息
            gpu_info = gpu_monitor.get_gpu_info(0)  # 监控第一个GPU
            
            if gpu_info['available']:
                # 发送GPU显存使用率信息到前端
                await websocket.send(json.dumps({
                    "type": "gpu-memory-usage",
                    **gpu_info
                }))
            else:
                # 发送错误信息
                await websocket.send(json.dumps({
                    "type": "gpu-memory-usage",
                    "available": False,
                    "error": gpu_info.get('error', '未知错误')
                }))
            
            # 等待指定间隔
            await asyncio.sleep(interval)
            
    except asyncio.CancelledError:
        print("GPU显存监测任务已取消")
    except Exception as e:
        print(f"GPU显存监测任务出错: {e}")

def get_gpu_status() -> Dict[str, Any]:
    """获取当前GPU显存状态（同步版本）"""
    return gpu_monitor.get_gpu_info(0) if gpu_monitor.initialized else {
        'available': False,
        'error': 'GPU显存监测器未初始化'
    } 