from abc import ABC, abstractmethod
from typing import List, Tuple, Any, Optional
from dataclasses import dataclass
import random


@dataclass
class WorkloadStats:
    total_operations: int
    num_gets: int
    num_puts: int
    unique_keys: int
    
    @property
    def read_write_ratio(self) -> float:
        #Calcula la proporción de lecturas.
        return self.num_gets / self.total_operations if self.total_operations > 0 else 0.0
    
    def to_dict(self) -> dict:
        #Convierte a diccionario.
        return {
            'total_operations': self.total_operations,
            'num_gets': self.num_gets,
            'num_puts': self.num_puts,
            'unique_keys': self.unique_keys,
            'read_write_ratio': self.read_write_ratio
        }


class Workload(ABC):
    
    def __init__(self, 
                 num_keys: int,
                 num_operations: int,
                 read_ratio: float = 0.8,
                 key_prefix: str = "key"):
        
        if num_keys <= 0:
            raise ValueError("num_keys debe ser positivo")
        if num_operations <= 0:
            raise ValueError("num_operations debe ser positivo")
        if not 0 <= read_ratio <= 1:
            raise ValueError("read_ratio debe estar entre 0 y 1")
        
        self._num_keys = num_keys
        self._num_operations = num_operations
        self._read_ratio = read_ratio
        self._key_prefix = key_prefix
        
        # Generar las claves que usaremos
        self._keys = [f"{key_prefix}_{i}" for i in range(num_keys)]
    
    @abstractmethod
    def _generate_key_sequence(self) -> List[str]:
        pass
    
    def generate(self) -> List[Tuple[str, str, Optional[Any]]]:
        # Generar secuencia de claves según el patrón
        key_sequence = self._generate_key_sequence()
        
        operations = []
        for key in key_sequence:
            # Decidir si es GET o PUT según read_ratio
            if random.random() < self._read_ratio:
                operations.append(('get', key, None))
            else:
                # Para PUT, generar un valor simple
                value = f"value_for_{key}_{random.randint(0, 9999)}"
                operations.append(('put', key, value))
        
        return operations
    
    def get_stats(self) -> WorkloadStats:
        # Generar para contar estadísticas
        operations = self.generate()
        
        num_gets = sum(1 for op, _, _ in operations if op == 'get')
        num_puts = len(operations) - num_gets
        unique_keys = len(set(key for _, key, _ in operations))
        
        return WorkloadStats(
            total_operations=len(operations),
            num_gets=num_gets,
            num_puts=num_puts,
            unique_keys=unique_keys
        )
    
    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(keys={self._num_keys}, "
                f"ops={self._num_operations}, read_ratio={self._read_ratio:.0%})")


class UniformWorkload(Workload):
    
    def _generate_key_sequence(self) -> List[str]:
        return [random.choice(self._keys) for _ in range(self._num_operations)]


class ZipfianWorkload(Workload):
   
    def __init__(self,
                 num_keys: int,
                 num_operations: int,
                 read_ratio: float = 0.8,
                 theta: float = 0.99,
                 key_prefix: str = "key"):
        super().__init__(num_keys, num_operations, read_ratio, key_prefix)
        self._theta = theta
        
        # Pre-calcular la distribución de probabilidades
        self._probabilities = self._calculate_zipfian_probabilities()
    
    def _calculate_zipfian_probabilities(self) -> List[float]:
        # Calcular el normalizador (constante de Zipf)
        normalizer = sum(1.0 / (i ** self._theta) for i in range(1, self._num_keys + 1))
        
        # Calcular probabilidades para cada rango
        probabilities = []
        for rank in range(1, self._num_keys + 1):
            prob = (1.0 / (rank ** self._theta)) / normalizer
            probabilities.append(prob)
        
        return probabilities
    
    def _generate_key_sequence(self) -> List[str]:
        #Genera secuencia con distribución Zipfian.
        # Usar random.choices con pesos para generar según probabilidades
        return random.choices(
            self._keys,
            weights=self._probabilities,
            k=self._num_operations
        )


class SequentialWorkload(Workload):
   
    def __init__(self,
                 num_keys: int,
                 num_operations: int,
                 read_ratio: float = 0.9,
                 num_passes: int = 1,
                 key_prefix: str = "key"):
        super().__init__(num_keys, num_operations, read_ratio, key_prefix)
        self._num_passes = num_passes
    
    def _generate_key_sequence(self) -> List[str]:
        sequence = []
        
        # Generar pasadas completas
        for _ in range(self._num_passes):
            sequence.extend(self._keys)
        
        # Si necesitamos más operaciones, agregar parcialmente
        remaining = self._num_operations - len(sequence)
        if remaining > 0:
            sequence.extend(self._keys[:remaining])
        
        # Si generamos demasiadas, truncar
        return sequence[:self._num_operations]

def create_workload(workload_type: str, num_keys: int, num_operations: int, **kwargs) -> Workload:
    workload_classes = {
        'uniform': UniformWorkload,
        'zipfian': ZipfianWorkload,
        'sequential': SequentialWorkload,
    }
    
    workload_class = workload_classes.get(workload_type.lower())
    if workload_class is None:
        raise ValueError(f"Tipo de workload desconocido: {workload_type}. "
                        f"Opciones disponibles: {list(workload_classes.keys())}")
    
    return workload_class(num_keys, num_operations, **kwargs)

if __name__ == "__main__":
    print("=== Demostración de Generadores de Workload ===\n")
    
    num_keys = 50
    num_ops = 200
    
    workloads = [
        UniformWorkload(num_keys, num_ops),
        ZipfianWorkload(num_keys, num_ops, theta=0.99),
        SequentialWorkload(num_keys, num_ops),
    ]
    
    print(f"Comparando workloads con {num_keys} claves y {num_ops} operaciones:\n")
    print(f"{'Workload':<20} {'Ops':<8} {'GETs':<8} {'PUTs':<8} {'Claves únicas':<15} {'R/W Ratio'}")
    print("-" * 85)
    
    for workload in workloads:
        stats = workload.get_stats()
        print(f"{workload.__class__.__name__:<20} "
              f"{stats.total_operations:<8} "
              f"{stats.num_gets:<8} "
              f"{stats.num_puts:<8} "
              f"{stats.unique_keys:<15} "
              f"{stats.read_write_ratio:.2%}")
    
    print("\n\nEjemplo de secuencia Zipfian (primeras 20 operaciones):")
    print("-" * 60)
    zipf = ZipfianWorkload(20, 20, read_ratio=0.8)
    ops = zipf.generate()
    for i, (op_type, key, _) in enumerate(ops[:20], 1):
        print(f"{i:2}. {op_type.upper():<4} {key}")
    
    print("\n\nEjemplo de secuencia Sequential (primeras 20 operaciones):")
    print("-" * 60)
    seq = SequentialWorkload(10, 20, read_ratio=0.9, num_passes=2)
    ops = seq.generate()
    for i, (op_type, key, _) in enumerate(ops[:20], 1):
        print(f"{i:2}. {op_type.upper():<4} {key}")
    
    print("\n=== Fin de la demostración ===")