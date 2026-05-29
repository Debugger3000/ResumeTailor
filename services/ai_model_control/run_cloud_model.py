from const.ai_models import ModelProvider
from services.ai_model_control.claude_client import claude_client


def start_cloud_model(model: ModelProvider) -> None:
    # set claude_client global class instances fields to set model provider found within db
    claude_client.configure(model)