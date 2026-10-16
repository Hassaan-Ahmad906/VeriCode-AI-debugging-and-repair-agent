"""Versioned repair configurations; hosted providers require a funded connection."""

from dataclasses import asdict, dataclass, field

from vericode.model_io import GenerationLimits, identifier
from vericode.feedback import FeedbackLimits
from vericode.sandbox_policy import DEFAULT_IMAGE, ExecutionLimits, validate_image_name
from vericode.schemas import ValidationError, require_fields, require_version


@dataclass(frozen=True)
class RunConfiguration:
    provider: str = "mock"
    model: str = "scripted-v1"
    backend: str = "mock"
    image: str = DEFAULT_IMAGE
    generation: GenerationLimits = field(default_factory=GenerationLimits)
    execution: ExecutionLimits = field(default_factory=ExecutionLimits)

    def __post_init__(self) -> None:
        if self.provider not in ("mock", "ollama", "openai", "openrouter"):
            raise ValidationError("provider: select mock, ollama, openai or openrouter")
        identifier(self.model, "model")
        if self.provider == "ollama" and (any(c in self.model for c in ("/", "\\", "@")) or "cloud" in self.model.lower()):
            raise ValidationError("model: cloud aliases and URLs are disabled")
        if self.backend not in ("mock", "docker"):
            raise ValidationError("backend: expected mock or docker")
        validate_image_name(self.image)
        if not isinstance(self.generation, GenerationLimits) or not isinstance(self.execution, ExecutionLimits):
            raise ValidationError("generation/execution: expected validated limit objects")

    def to_dict(self) -> dict:
        return {"schema_version": 1, "strategy": "direct", **asdict(self)}

    @property
    def strategy(self) -> str:
        return "direct"

    @classmethod
    def from_dict(cls, data: dict) -> "RunConfiguration":
        if isinstance(data, dict) and data.get("strategy") == "augmented":
            return AugmentedConfiguration.from_dict(data)
        if isinstance(data, dict) and data.get("strategy") == "feedback":
            return FeedbackConfiguration.from_dict(data)
        data = require_fields(data, {"schema_version", "strategy", *cls.__dataclass_fields__}, "run configuration")
        require_version(data["schema_version"])
        if data["strategy"] != "direct":
            raise ValidationError("strategy: expected direct or feedback")
        generation = require_fields(data["generation"], set(GenerationLimits.__dataclass_fields__), "generation limits")
        execution = require_fields(data["execution"], set(ExecutionLimits.__dataclass_fields__), "execution limits")
        return cls(data["provider"], data["model"], data["backend"], data["image"],
                   GenerationLimits(**generation), ExecutionLimits(**execution))


@dataclass(frozen=True)
class FeedbackConfiguration(RunConfiguration):
    feedback: FeedbackLimits = field(default_factory=FeedbackLimits)

    def __post_init__(self) -> None:
        super().__post_init__()
        if not isinstance(self.feedback, FeedbackLimits):
            raise ValidationError("feedback: expected validated FeedbackLimits")

    @property
    def strategy(self) -> str:
        return "feedback"

    def to_dict(self) -> dict:
        return {"schema_version": 2, "strategy": self.strategy, **asdict(self)}

    @classmethod
    def from_dict(cls, data: dict) -> "FeedbackConfiguration":
        data = require_fields(data, {"schema_version", "strategy", *cls.__dataclass_fields__}, "feedback configuration")
        if type(data["schema_version"]) is not int or data["schema_version"] != 2 or data["strategy"] != "feedback":
            raise ValidationError("feedback configuration: expected schema_version 2 and strategy feedback")
        generation = require_fields(data["generation"], set(GenerationLimits.__dataclass_fields__), "generation limits")
        execution = require_fields(data["execution"], set(ExecutionLimits.__dataclass_fields__), "execution limits")
        feedback = require_fields(data["feedback"], set(FeedbackLimits.__dataclass_fields__), "feedback limits")
        return cls(data["provider"], data["model"], data["backend"], data["image"],
                   GenerationLimits(**generation), ExecutionLimits(**execution), FeedbackLimits(**feedback))


@dataclass(frozen=True)
class AugmentedConfiguration(FeedbackConfiguration):
    @property
    def strategy(self) -> str:
        return "augmented"

    def to_dict(self) -> dict:
        return {"schema_version": 3, "strategy": self.strategy, **asdict(self)}

    @classmethod
    def from_dict(cls, data: dict) -> "AugmentedConfiguration":
        data = require_fields(data, {"schema_version", "strategy", *cls.__dataclass_fields__}, "augmented configuration")
        if type(data["schema_version"]) is not int or data["schema_version"] != 3 or data["strategy"] != "augmented":
            raise ValidationError("augmented configuration: expected schema_version 3 and strategy augmented")
        base = FeedbackConfiguration.from_dict({**data, "schema_version": 2, "strategy": "feedback"})
        return cls(base.provider, base.model, base.backend, base.image, base.generation, base.execution, base.feedback)
