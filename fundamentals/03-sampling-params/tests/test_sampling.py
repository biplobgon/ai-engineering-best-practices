"""
Tests for sampling parameters functionality.
"""

import pytest
from fundamentals.fundamentals_03_sampling_params.sampling_strategies import (
    SamplingStrategy,
    TaskType,
    STRATEGIES,
    get_adaptive_strategy,
)


class TestSamplingStrategy:
    """Tests for SamplingStrategy dataclass."""
    
    def test_strategy_creation(self):
        """Test creating a sampling strategy."""
        strategy = SamplingStrategy(
            name="Test",
            temperature=0.5,
            max_tokens=100,
            top_p=0.9,
        )
        
        assert strategy.name == "Test"
        assert strategy.temperature == 0.5
        assert strategy.max_tokens == 100
        assert strategy.top_p == 0.9
    
    def test_strategy_defaults(self):
        """Test default values."""
        strategy = SamplingStrategy(
            name="Test",
            temperature=0.5,
            max_tokens=100,
        )
        
        assert strategy.top_p == 1.0
        assert strategy.frequency_penalty == 0.0
        assert strategy.presence_penalty == 0.0
        assert strategy.stop is None


class TestPredefinedStrategies:
    """Tests for predefined sampling strategies."""
    
    def test_all_task_types_have_strategies(self):
        """Test that all task types have predefined strategies."""
        for task_type in TaskType:
            assert task_type in STRATEGIES
    
    def test_classification_strategy(self):
        """Test classification strategy is deterministic."""
        strategy = STRATEGIES[TaskType.CLASSIFICATION]
        
        assert strategy.temperature == 0.0  # Deterministic
        assert strategy.max_tokens <= 50  # Short output
        assert strategy.top_p <= 0.5  # Focused
    
    def test_creative_writing_strategy(self):
        """Test creative writing strategy is diverse."""
        strategy = STRATEGIES[TaskType.CREATIVE_WRITING]
        
        assert strategy.temperature >= 0.8  # Creative
        assert strategy.max_tokens >= 1000  # Long output
        assert strategy.frequency_penalty > 0  # Avoid repetition
    
    def test_code_generation_strategy(self):
        """Test code generation strategy."""
        strategy = STRATEGIES[TaskType.CODE_GENERATION]
        
        assert strategy.temperature <= 0.3  # Low creativity
        assert strategy.max_tokens >= 500  # Enough for code
        assert strategy.stop is not None  # Has stop sequences
    
    def test_chat_strategy(self):
        """Test general chat strategy is balanced."""
        strategy = STRATEGIES[TaskType.CHAT]
        
        assert 0.5 <= strategy.temperature <= 0.9  # Balanced
        assert strategy.max_tokens >= 200  # Decent length
    
    def test_all_strategies_valid_params(self):
        """Test all strategies have valid parameters."""
        for task_type, strategy in STRATEGIES.items():
            # Temperature range
            assert 0.0 <= strategy.temperature <= 2.0
            
            # Top-p range
            assert 0.0 <= strategy.top_p <= 1.0
            
            # Max tokens positive
            assert strategy.max_tokens > 0
            
            # Penalties in valid range
            assert -2.0 <= strategy.frequency_penalty <= 2.0
            assert -2.0 <= strategy.presence_penalty <= 2.0


class TestAdaptiveStrategy:
    """Tests for adaptive strategy function."""
    
    def test_adaptive_simple_task(self):
        """Test adaptive strategy for simple tasks."""
        base = STRATEGIES[TaskType.CHAT]
        adapted = get_adaptive_strategy(
            TaskType.CHAT,
            complexity="simple",
            budget="normal",
        )
        
        # Should reduce temperature and tokens for simple tasks
        assert adapted.temperature <= base.temperature
        assert adapted.max_tokens <= base.max_tokens
    
    def test_adaptive_complex_task(self):
        """Test adaptive strategy for complex tasks."""
        base = STRATEGIES[TaskType.CHAT]
        adapted = get_adaptive_strategy(
            TaskType.CHAT,
            complexity="complex",
            budget="normal",
        )
        
        # Should increase temperature and tokens for complex tasks
        assert adapted.temperature >= base.temperature
        assert adapted.max_tokens >= base.max_tokens
    
    def test_adaptive_low_budget(self):
        """Test adaptive strategy for low budget."""
        adapted = get_adaptive_strategy(
            TaskType.CHAT,
            complexity="medium",
            budget="low",
        )
        
        # Should cap max tokens for low budget
        assert adapted.max_tokens <= 200
    
    def test_adaptive_high_budget(self):
        """Test adaptive strategy for high budget."""
        base = STRATEGIES[TaskType.CHAT]
        adapted = get_adaptive_strategy(
            TaskType.CHAT,
            complexity="medium",
            budget="high",
        )
        
        # Should allow more tokens for high budget
        assert adapted.max_tokens >= base.max_tokens
    
    def test_adaptive_temperature_bounds(self):
        """Test that adaptive strategy respects temperature bounds."""
        # Even with complex task, should cap at 1.0
        adapted = get_adaptive_strategy(
            TaskType.CREATIVE_WRITING,  # Already high temp
            complexity="complex",
            budget="normal",
        )
        
        assert adapted.temperature <= 2.0  # Should not exceed max


class TestStrategyRecommendations:
    """Tests for strategy recommendations."""
    
    def test_deterministic_tasks_low_temp(self):
        """Test that deterministic tasks use low temperature."""
        deterministic_tasks = [
            TaskType.CLASSIFICATION,
            TaskType.EXTRACTION,
        ]
        
        for task in deterministic_tasks:
            strategy = STRATEGIES[task]
            assert strategy.temperature <= 0.3
    
    def test_creative_tasks_high_temp(self):
        """Test that creative tasks use higher temperature."""
        creative_tasks = [
            TaskType.CREATIVE_WRITING,
        ]
        
        for task in creative_tasks:
            strategy = STRATEGIES[task]
            assert strategy.temperature >= 0.8
    
    def test_short_output_tasks(self):
        """Test that classification/extraction have short max_tokens."""
        short_output_tasks = [
            TaskType.CLASSIFICATION,
        ]
        
        for task in short_output_tasks:
            strategy = STRATEGIES[task]
            assert strategy.max_tokens <= 100
    
    def test_long_output_tasks(self):
        """Test that writing/code tasks allow longer output."""
        long_output_tasks = [
            TaskType.CREATIVE_WRITING,
            TaskType.CODE_GENERATION,
            TaskType.ANALYSIS,
        ]
        
        for task in long_output_tasks:
            strategy = STRATEGIES[task]
            assert strategy.max_tokens >= 1000


class TestParameterInteractions:
    """Tests for parameter interaction understanding."""
    
    def test_temp_zero_is_deterministic(self):
        """Test understanding that temp=0.0 is deterministic."""
        strategy = STRATEGIES[TaskType.CLASSIFICATION]
        
        assert strategy.temperature == 0.0
        # With temp=0, top_p becomes less relevant
    
    def test_high_temp_with_low_topp(self):
        """Test that high temp + low top_p = focused creativity."""
        # Create a focused creative strategy
        strategy = SamplingStrategy(
            name="Focused Creative",
            temperature=1.0,
            max_tokens=500,
            top_p=0.5,
        )
        
        # High temp = creative
        assert strategy.temperature >= 0.8
        # Low top_p = focused vocabulary
        assert strategy.top_p <= 0.5
    
    def test_penalties_reduce_repetition(self):
        """Test that strategies use penalties for variety."""
        variety_tasks = [
            TaskType.CHAT,
            TaskType.CREATIVE_WRITING,
        ]
        
        for task in variety_tasks:
            strategy = STRATEGIES[task]
            # At least one penalty should be positive
            assert (strategy.frequency_penalty > 0 or
                   strategy.presence_penalty > 0)


class TestTaskTypeEnum:
    """Tests for TaskType enum."""
    
    def test_all_task_types_valid(self):
        """Test that all task types are valid enum values."""
        task_types = [
            TaskType.CLASSIFICATION,
            TaskType.EXTRACTION,
            TaskType.SUMMARIZATION,
            TaskType.QA,
            TaskType.CHAT,
            TaskType.CREATIVE_WRITING,
            TaskType.CODE_GENERATION,
            TaskType.ANALYSIS,
        ]
        
        for task_type in task_types:
            assert isinstance(task_type, TaskType)
            assert task_type.value is not None
