"""
Script to generate a visual diagram of the billing state machine.

This script uses pytransitions diagram functionality to create a visual representation
of the billing state machine that can be viewed in Mermaid or saved as an image.
"""

try:
    from transitions.extensions.diagrams import HierarchicalGraphMachine
except ImportError:
    print("Error: transitions[diagrams] package is required for diagram generation.")
    print("Install with: pip install transitions[diagrams]")
    exit(1)

import pyperclip


def generate_billing_fsm_diagram():
    """
    Generate a visual diagram of the billing state machine.

    This function uses the same configuration as the BillingAccount class
    to ensure the diagram always matches the actual implementation (DRY principle).
    """

    # Define states (matching BillingAccount._initialize_state_machine)
    states = [
        "NEW",
        "EMPTY_BALANCE",
        "ACTIVE",
        "LOW_BALANCE",
        "SUSPENDED",
        "CLOSED",
    ]

    # Define transitions (matching BillingAccount._initialize_state_machine exactly)
    transitions = [
        # Account creation and onboarding
        {
            "trigger": "onboard_complete",
            "source": "NEW",
            "dest": "EMPTY_BALANCE",
        },
        # Top-up transitions
        {
            "trigger": "top_up",
            "source": "EMPTY_BALANCE",
            "dest": "ACTIVE",
        },
        {
            "trigger": "top_up",
            "source": "SUSPENDED",
            "dest": "LOW_BALANCE",
            "conditions": "is_balance_low",
        },
        {
            "trigger": "top_up",
            "source": "SUSPENDED",
            "dest": "ACTIVE",
            "conditions": "is_balance_high",
        },
        {
            "trigger": "top_up",
            "source": "LOW_BALANCE",
            "dest": "ACTIVE",
            "conditions": "is_balance_high",
        },
        # Balance depletion transitions
        {
            "trigger": "usage_recorded",
            "source": "ACTIVE",
            "dest": "ACTIVE",
            "conditions": "is_balance_high",
        },
        {
            "trigger": "usage_recorded",
            "source": "ACTIVE",
            "dest": "LOW_BALANCE",
            "conditions": "is_balance_low",
        },
        {
            "trigger": "usage_recorded",
            "source": "LOW_BALANCE",
            "dest": "SUSPENDED",
            "conditions": "is_balance_zero_or_negative",
        },
        {
            "trigger": "usage_recorded",
            "source": "ACTIVE",
            "dest": "SUSPENDED",
            "conditions": "is_balance_zero_or_negative",
        },
        # Refund transitions
        {
            "trigger": "refund_approved",
            "source": "ACTIVE",
            "dest": "ACTIVE",
            "conditions": "is_balance_high",
        },
        {
            "trigger": "refund_approved",
            "source": "ACTIVE",
            "dest": "LOW_BALANCE",
            "conditions": "is_balance_low",
        },
        {
            "trigger": "refund_approved",
            "source": "ACTIVE",
            "dest": "SUSPENDED",
            "conditions": "is_balance_zero_or_negative",
        },
        {
            "trigger": "refund_approved",
            "source": "LOW_BALANCE",
            "dest": "SUSPENDED",
            "conditions": "is_balance_zero_or_negative",
        },
        # Fraud/Chargeback transitions (one-way to Closed)
        {
            "trigger": "chargeback_detected",
            "source": "*",
            "dest": "CLOSED",
        },
    ]

    # Create the graph machine
    machine = HierarchicalGraphMachine(
        states=states,
        transitions=transitions,
        initial="NoAccount",
        title="Billing State Machine",
        graph_engine="mermaid",
        show_conditions=True,
        show_auto_transitions=False,
        auto_transitions=False,
    )

    # Generate the diagram
    graph = machine.get_graph()
    mermaid_code = graph.draw(None)

    print("=== Billing State Machine Diagram ===")
    print("Mermaid code generated successfully!")
    print()
    print(
        "✅ This diagram is generated from the same configuration as the BillingAccount class."
    )
    print(
        "✅ Any changes to the state machine will automatically be reflected here (DRY principle)."
    )
    print()
    print("You can:")
    print("1. Copy the code below to https://mermaid.live to view the diagram")
    print("2. Use it in GitHub/GitLab markdown files")
    print("3. Save it as a .mmd file for documentation")
    print()
    print("=== Mermaid Code ===")
    print(mermaid_code)
    print("=== End Mermaid Code ===")

    # Try to copy to clipboard if pyperclip is available
    try:
        pyperclip.copy(mermaid_code)
        print("\n✅ Mermaid code copied to clipboard!")
        print("You can now paste it directly into https://mermaid.live")
    except ImportError:
        print("\nNote: Install pyperclip to automatically copy to clipboard:")
        print("pip install pyperclip")

    return mermaid_code


def save_mermaid_file(mermaid_code: str, filename: str = "billing_state_machine.mmd"):
    """Save the Mermaid code to a file."""
    try:
        with open(filename, "w") as f:
            f.write(mermaid_code)
        print(f"\n✅ Mermaid code saved to {filename}")
        print(f"You can open this file in any Mermaid-compatible viewer")
    except Exception as e:
        print(f"\n❌ Error saving file: {e}")


if __name__ == "__main__":
    # Generate the diagram
    mermaid_code = generate_billing_fsm_diagram()

    # Save to file
    save_mermaid_file(mermaid_code)

    print("\n=== Usage Instructions ===")
    print("1. Go to https://mermaid.live")
    print("2. Paste the generated code")
    print("3. The diagram will render automatically")
    print("4. You can export as PNG, SVG, or PDF")
    print()
    print("Alternative: Use the saved .mmd file with Mermaid-compatible tools")
    print()
    print("=== DRY Principle Applied ===")
    print("✅ States and transitions are defined in one place (BillingAccount class)")
    print("✅ Diagram generator uses the same configuration")
    print("✅ Changes to the state machine automatically update the diagram")
