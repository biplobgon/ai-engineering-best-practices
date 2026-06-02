"""
System messages and role definitions.

Pre-built personas for common roles.

Status: Placeholder for Phase 3 expansion
"""

import logging


logger = logging.getLogger(__name__)

# System message library
ROLES = {
    "technical_assistant": "You are a technical assistant with deep expertise in software engineering.",
    "research_analyst": "You are a research analyst skilled at analyzing data and drawing insights.",
    "code_reviewer": "You are an experienced code reviewer focused on quality and best practices.",
    "customer_support": "You are a friendly customer support agent helping users solve problems.",
    "data_scientist": "You are a data scientist expert in statistics, ML, and data analysis.",
    "product_manager": "You are a product manager focused on user needs and business value.",
    "creative_writer": "You are a creative writer skilled at engaging storytelling.",
    "educator": "You are an educator skilled at explaining complex topics clearly.",
}


def get_role(role_name: str) -> str:
    """
    Get system message for role.

    Args:
        role_name: Role name

    Returns:
        System message

    Example:
        >>> system_msg = get_role("data_scientist")
        >>> print(system_msg)
    """
    if role_name in ROLES:
        return ROLES[role_name]

    logger.warning(f"Unknown role: {role_name}, using default")
    return "You are a helpful assistant."


def list_roles() -> list[str]:
    """List available roles."""
    return list(ROLES.keys())


def main():
    """Demo system messages."""
    print("System Messages Library")
    print("=" * 60)

    print("\nAvailable roles:")
    for role in list_roles():
        print(f"\n{role}:")
        print(f"  {get_role(role)}")


if __name__ == "__main__":
    main()
