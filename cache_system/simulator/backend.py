from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum

class StorageType(Enum):
    CPU_CACHE = "cpu_cache"
    MEMORY = "memory"
    SSD = "ssd"
    HDD = "hdd"
    NETWORK = "network"

@dataclass
class Backend:
    name: str
    storage_type: StorageType
    latency_ms: float
    capacity_mb: Optional[int] = None
    throughput_mbps: Optional[int] = None
    description: Optional[str] = None

    def __post_init__(self):
        if self.description is None:
            self.description = self._generate_description()
    
    def _generate_description(self) -> str:
        parts = [f"{self.storage_type.value.upper()}"]
        
        if self.capacity_mb:
            if self.capacity_mb >= 1024:
                parts.append(f"{self.capacity_mb // 1024}GB")
            else:
                parts.append(f"{self.capacity_mb}MB")
        
        parts.append(f"{self.latency_ms}ms latency")
        
        if self.throughput_mbps:
            if self.throughput_mbps >= 1024:
                parts.append(f"{self.throughput_mbps // 1024}GB/s")
            else:
                parts.append(f"{self.throughput_mbps}MB/s")
        
        return " - ".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'storage_type': self.storage_type.value,
            'latency_ms': self.latency_ms,
            'capacity_mb': self.capacity_mb,
            'throughput_mbps': self.throughput_mbps,
            'description': self.description
        }
    
    def __repr__(self) -> str:
        return f"Backend(name='{self.name}', type={self.storage_type.value}, latency={self.latency_ms}ms)"
    

class CPUCacheBackend(Backend):
    def __init__(self, name: str = "CPU Cache", level : int = 1, capacity_mb: float= 0.032):
        latencies = {
            1: 0.001,
            2: 0.003,
            3: 0.010,
        }
        super().__init__(
            name=name,
            storage_type=StorageType.CPU_CACHE,
            latency_ms=latencies.get(level, 0.001),
            capacity_mb=capacity_mb,
            throughput_mbps=100000,
            description=f"L{level} CPU Cache"
        )

class MemoryBackend(Backend):
    def __init__(self,
                 name: str = "RAM",
                 latency_ms: float = 0.1,
                 capacity_mb: int = 16384, 
                 ddr_generation: int = 4):
     
        throughputs = {
            3: 17000, 
            4: 25000,   
            5: 40000,   
        }
        
        super().__init__(
            name=name,
            storage_type=StorageType.MEMORY,
            latency_ms=latency_ms,
            capacity_mb=capacity_mb,
            throughput_mbps=throughputs.get(ddr_generation, 25000),
            description=f"DDR{ddr_generation} RAM"
        )

class SSDBackend(Backend):
    
    def __init__(self,
                 name: str = "SSD",
                 latency_ms: float = 0.5,
                 capacity_mb: int = 512000,  # 500GB default
                 interface: str = "nvme"):
     
        configs = {
            'nvme': {'throughput': 3500, 'typical_latency': 0.1},  
            'sata': {'throughput': 550, 'typical_latency': 1.0},   
        }
        
        config = configs.get(interface.lower(), configs["nvme"])
        
        super().__init__(
            name=name,
            storage_type=StorageType.SSD,
            latency_ms=latency_ms,
            capacity_mb=capacity_mb,
            throughput_mbps=config['throughput'],
            description=f"{interface.upper()} SSD"
        )

class HDDBackend(Backend):
    
    def __init__(self,
                 name: str = "HDD",
                 latency_ms: float = 10.0,
                 capacity_mb: int = 4000000,  
                 rpm: int = 7200):
     
        typical_latencies = {
            5400: 11.0,  
            7200: 8.5,    
            10000: 6.0,   
        }
        
        
        throughputs = {
            5400: 120,    
            7200: 160,    
            10000: 200,  
        }
        
        super().__init__(
            name=name,
            storage_type=StorageType.HDD,
            latency_ms=latency_ms,
            capacity_mb=capacity_mb,
            throughput_mbps=throughputs.get(rpm, 160),
            description=f"{rpm}RPM HDD"
        )

class NetworkBackend(Backend):
  
    
    def __init__(self,
                 name: str = "Network",
                 latency_ms: float = 50.0,
                 capacity_mb: Optional[int] = None,  
                 network_type: str = "lan"):
        
        configs = {
            'lan': {'throughput': 125, 'typical_latency': 1.0},      
            'wan': {'throughput': 12, 'typical_latency': 50.0},      
            'cloud': {'throughput': 50, 'typical_latency': 100.0},   
        }
        
        config = configs.get(network_type.lower(), configs['lan'])
        
        super().__init__(
            name=name,
            storage_type=StorageType.NETWORK,
            latency_ms=latency_ms,
            capacity_mb=capacity_mb,
            throughput_mbps=config['throughput'],
            description=f"{network_type.upper()} Storage"
        )
    
def create_typical_hierarchy() -> Dict[str, Backend]:
    
    return {
        'L1': MemoryBackend(name="L1-RAM", latency_ms=1, capacity_mb=1024),
        'L2': SSDBackend(name="L2-SSD", latency_ms=5, capacity_mb=10240, interface="nvme"),
        'L3': HDDBackend(name="L3-HDD", latency_ms=50, capacity_mb=100000, rpm=7200)
    }


def create_cloud_hierarchy() -> Dict[str, Backend]:
    return {
        'L1': MemoryBackend(name="Local-RAM", latency_ms=0.5, capacity_mb=2048),
        'L2': SSDBackend(name="Local-SSD", latency_ms=2, capacity_mb=20480, interface="nvme"),
        'L3': NetworkBackend(name="Cloud-Storage", latency_ms=100, network_type="cloud")
    }


def get_backend_by_type(storage_type: StorageType, **kwargs) -> Backend:
    backend_classes = {
        StorageType.CPU_CACHE: CPUCacheBackend,
        StorageType.MEMORY: MemoryBackend,
        StorageType.SSD: SSDBackend,
        StorageType.HDD: HDDBackend,
        StorageType.NETWORK: NetworkBackend,
    }
    
    backend_class = backend_classes.get(storage_type)
    if backend_class is None:
        raise ValueError(f"Tipo de almacenamiento desconocido: {storage_type}")
    
    return backend_class(**kwargs)

if __name__ == "__main__":
    print("=== Demostración de Backends de Almacenamiento ===\n")
    
    print("1. Backends individuales:")
    print("-" * 60)
    
    ram = MemoryBackend()
    print(f"RAM: {ram.description}")
    print(f"  Latencia: {ram.latency_ms}ms")
    print(f"  Capacidad: {ram.capacity_mb}MB")
    print(f"  Throughput: {ram.throughput_mbps}MB/s\n")
    
    ssd = SSDBackend(interface="nvme")
    print(f"SSD: {ssd.description}")
    print(f"  Latencia: {ssd.latency_ms}ms")
    print(f"  Capacidad: {ssd.capacity_mb}MB")
    print(f"  Throughput: {ssd.throughput_mbps}MB/s\n")
    
    hdd = HDDBackend(rpm=7200)
    print(f"HDD: {hdd.description}")
    print(f"  Latencia: {hdd.latency_ms}ms")
    print(f"  Capacidad: {hdd.capacity_mb}MB")
    print(f"  Throughput: {hdd.throughput_mbps}MB/s\n")
    
    print("\n2. Jerarquía típica:")
    print("-" * 60)
    
    hierarchy = create_typical_hierarchy()
    for level_name, backend in hierarchy.items():
        print(f"{level_name}: {backend}")
        print(f"  {backend.description}")
    
    print("\n3. Comparación de latencias:")
    print("-" * 60)
    print(f"{'Backend':<20} {'Latencia (ms)':<15} {'Diferencia vs L1'}")
    print("-" * 60)
    
    l1_latency = hierarchy['L1'].latency_ms
    for level_name, backend in hierarchy.items():
        diff = backend.latency_ms - l1_latency
        print(f"{backend.name:<20} {backend.latency_ms:<15.2f} {diff:>6.2f}ms más lento")
    
    print("\n=== Fin de la demostración ===")
