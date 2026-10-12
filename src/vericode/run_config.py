"""Recorded configuration for direct repair; paid providers remain unavailable."""

from dataclasses import asdict, dataclass, field

from vericode.model_io import GenerationLimits, identifier
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
        if self.provider != "mock":
            raise ValidationError("provider: only mock is enabled; paid adapters require budget configuration")
        identifier(self.model, "model")
        if self.backend not in ("mock", "docker"):
            raise ValidationError("backend: expected mock or docker")
        validate_image_name(self.image)
        if not isinstance(self.generation, GenerationLimits) or not isinstance(self.execution, ExecutionLimits):
            raise ValidationError("generation/execution: expected validated limit objects")

    def to_dict(self) -> dict:
        return {"schema_version": 1, "strategy": "direct", **asdict(self)}

    @classmethod
    def from_dict(cls, data: dict) -> "RunConfiguration":
        data = require_fields(data, {"schema_version", "strategy", *cls.__dataclass_fields__}, "run configuration")
        require_version(data["schema_version"])
        if data["strategy"] != "direct":
            raise ValidationError("strategy: only direct repair is implemented")
        generation = require_fields(data["generation"], set(GenerationLimits.__dataclass_fields__), "generation limits")
        execution = require_fields(data["execution"], set(ExecutionLimits.__dataclass_fields__), "execution limits")
        return cls(data["provider"], data["model"], data["backend"], data["image"],
                   GenerationLimits(**generation), ExecutionLimits(**execution))
