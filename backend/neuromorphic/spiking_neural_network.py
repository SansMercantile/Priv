# backend/neuromorphic/spiking_neural_network.py
"""
Software-based Spiking Neural Network (SNN)

Implements neuromorphic computing in software without requiring specialized hardware.
Uses standard GPUs/CPUs to simulate spiking neurons and temporal coding.
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)


@dataclass
class NeuronState:
    """State of a spiking neuron"""
    membrane_potential: float
    threshold: float
    refractory_period: int
    last_spike_time: float


class LeakyIntegrateFireNeuron:
    """
    Leaky Integrate-and-Fire (LIF) neuron model.
    
    This is the most common spiking neuron model, simulating:
    - Membrane potential integration
    - Spike generation when threshold is reached
    - Refractory period after spiking
    - Membrane potential leak over time
    """
    
    def __init__(
        self,
        threshold: float = 1.0,
        leak_factor: float = 0.95,
        refractory_period: int = 5,
        reset_potential: float = 0.0
    ):
        self.threshold = threshold
        self.leak_factor = leak_factor
        self.refractory_period = refractory_period
        self.reset_potential = reset_potential
        
        self.membrane_potential = 0.0
        self.time_since_spike = float('inf')
    
    def update(self, input_current: float, dt: float = 1.0) -> bool:
        """
        Update neuron state and return True if spike occurred.
        
        Args:
            input_current: Input current to the neuron
            dt: Time step
        
        Returns:
            True if neuron spiked, False otherwise
        """
        # Check if in refractory period
        if self.time_since_spike < self.refractory_period:
            self.time_since_spike += dt
            return False
        
        # Leak membrane potential
        self.membrane_potential *= self.leak_factor
        
        # Add input current
        self.membrane_potential += input_current * dt
        
        # Check for spike
        if self.membrane_potential >= self.threshold:
            self.membrane_potential = self.reset_potential
            self.time_since_spike = 0.0
            return True
        
        self.time_since_spike += dt
        return False


class SpikingNeuralNetwork:
    """
    Software-based Spiking Neural Network for pattern recognition.
    
    Can run on standard hardware (CPU/GPU) without specialized neuromorphic chips.
    """
    
    def __init__(
        self,
        input_size: int,
        hidden_sizes: List[int],
        output_size: int,
        use_gpu: bool = True
    ):
        """
        Initialize the SNN.
        
        Args:
            input_size: Number of input neurons
            hidden_sizes: List of hidden layer sizes
            output_size: Number of output neurons
            use_gpu: Use GPU acceleration if available
        """
        self.input_size = input_size
        self.hidden_sizes = hidden_sizes
        self.output_size = output_size
        self.use_gpu = use_gpu and torch.cuda.is_available()
        
        self.device = torch.device("cuda" if self.use_gpu else "cpu")
        
        # Create layers of LIF neurons
        self.layers: List[List[LeakyIntegrateFireNeuron]] = []
        layer_sizes = [input_size] + hidden_sizes + [output_size]
        
        for size in layer_sizes[1:]:
            layer = [LeakyIntegrateFireNeuron() for _ in range(size)]
            self.layers.append(layer)
        
        # Create weight matrices
        self.weights: List[torch.Tensor] = []
        for i in range(len(layer_sizes) - 1):
            weight = torch.randn(
                layer_sizes[i+1],
                layer_sizes[i],
                device=self.device
            ) * 0.1
            self.weights.append(weight)
        
        logger.info(f"SNN initialized: {layer_sizes} (GPU: {self.use_gpu})")
    
    def forward(
        self,
        spike_train: np.ndarray,
        time_steps: int = 100
    ) -> Tuple[np.ndarray, List[List[float]]]:
        """
        Process a spike train through the network.
        
        Args:
            spike_train: Input spike train (time_steps x input_size)
            time_steps: Number of time steps to simulate
        
        Returns:
            Tuple of (output_spikes, membrane_potentials)
        """
        # Convert to tensor
        spike_train_tensor = torch.tensor(
            spike_train,
            dtype=torch.float32,
            device=self.device
        )
        
        # Track output spikes
        output_spikes = np.zeros((time_steps, self.output_size))
        membrane_potentials = [[] for _ in range(len(self.layers))]
        
        # Simulate for each time step
        for t in range(time_steps):
            # Get input spikes for this time step
            if t < len(spike_train):
                layer_input = spike_train_tensor[t]
            else:
                layer_input = torch.zeros(self.input_size, device=self.device)
            
            # Propagate through layers
            for layer_idx, (layer, weights) in enumerate(zip(self.layers, self.weights)):
                # Calculate input currents
                currents = torch.matmul(weights, layer_input).cpu().numpy()
                
                # Update neurons and collect spikes
                layer_spikes = []
                layer_potentials = []
                
                for neuron_idx, (neuron, current) in enumerate(zip(layer, currents)):
                    spiked = neuron.update(current)
                    layer_spikes.append(1.0 if spiked else 0.0)
                    layer_potentials.append(neuron.membrane_potential)
                
                # Store membrane potentials
                membrane_potentials[layer_idx].append(layer_potentials)
                
                # Use spikes as input to next layer
                layer_input = torch.tensor(
                    layer_spikes,
                    dtype=torch.float32,
                    device=self.device
                )
            
            # Store output layer spikes
            output_spikes[t] = layer_input.cpu().numpy()
        
        return output_spikes, membrane_potentials
    
    def train_stdp(
        self,
        spike_train: np.ndarray,
        target_pattern: np.ndarray,
        learning_rate: float = 0.01
    ):
        """
        Train using Spike-Timing-Dependent Plasticity (STDP).
        
        STDP is a biologically-inspired learning rule where:
        - Weights increase if pre-synaptic spike precedes post-synaptic spike
        - Weights decrease if post-synaptic spike precedes pre-synaptic spike
        """
        # This is a simplified STDP implementation
        # In practice, you'd track precise spike timings
        
        output_spikes, _ = self.forward(spike_train)
        
        # Calculate error
        error = target_pattern - output_spikes.sum(axis=0)
        
        # Update weights (simplified)
        for i, weight in enumerate(self.weights):
            # Gradient-based update (simplified STDP)
            weight_update = learning_rate * torch.tensor(
                error,
                dtype=torch.float32,
                device=self.device
            ).unsqueeze(1)
            self.weights[i] += weight_update
    
    def save(self, path: str):
        """Save network weights"""
        torch.save({
            'weights': [w.cpu() for w in self.weights],
            'config': {
                'input_size': self.input_size,
                'hidden_sizes': self.hidden_sizes,
                'output_size': self.output_size
            }
        }, path)
    
    def load(self, path: str):
        """Load network weights"""
        checkpoint = torch.load(path)
        self.weights = [w.to(self.device) for w in checkpoint['weights']]

