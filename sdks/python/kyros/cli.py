#!/usr/bin/env python3
"""Kyros CLI tool for debugging and testing.

This CLI provides commands for inspecting memories, profiling performance,
generating test data, and running integration tests.

Usage:
    kyros inspect <agent_id>              # Inspect agent memories
    kyros compare <agent1> <agent2> ...   # Compare multiple agents
    kyros generate --agents 10 --memories 20  # Generate test data
    kyros test                            # Run integration tests
    kyros load-test --agents 5            # Load test data into Kyros

Examples:
    # Inspect memories for an agent
    kyros inspect user123

    # Compare two agents
    kyros compare user123 user456

    # Generate test data
    kyros generate --agents 10 --memories 50

    # Run integration tests
    kyros test --agent test-user
"""

import argparse
import os
import sys

from .client import KyrosClient
from .debug import MemoryInspector, PerformanceProfiler
from .testing import TestDataGenerator, load_test_data, run_integration_test


def get_client() -> KyrosClient:
    """Get Kyros client from environment.

    Returns:
        Configured KyrosClient

    Raises:
        SystemExit: If KYROS_API_KEY not set
    """
    api_key = os.getenv("KYROS_API_KEY")
    if not api_key:
        print("❌ Error: KYROS_API_KEY environment variable not set")
        print("\nSet it with:")
        print("  export KYROS_API_KEY=your-api-key")
        sys.exit(1)

    base_url = os.getenv("KYROS_BASE_URL", "http://localhost:8000")
    return KyrosClient(api_key=api_key, base_url=base_url)


def cmd_inspect(args: argparse.Namespace) -> None:
    """Inspect agent memories.

    Args:
        args: Command arguments
    """
    client = get_client()
    inspector = MemoryInspector(client)

    report = inspector.inspect_agent(args.agent_id, detailed=args.detailed)

    if args.output:
        import json
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n✅ Report saved to: {args.output}")


def cmd_compare(args: argparse.Namespace) -> None:
    """Compare multiple agents.

    Args:
        args: Command arguments
    """
    client = get_client()
    inspector = MemoryInspector(client)

    comparison = inspector.compare_agents(args.agent_ids)

    print("\n" + "=" * 60)
    print("AGENT COMPARISON")
    print("=" * 60)

    for agent_id, summary in comparison["summary"].items():
        print(f"\n{agent_id}:")
        print(f"  Total Memories: {summary['total']}")
        print(f"  Avg Importance: {summary['avg_importance']:.2f}")

    print("\n" + "=" * 60)

    if args.output:
        import json
        with open(args.output, "w") as f:
            json.dump(comparison, f, indent=2)
        print(f"\n✅ Comparison saved to: {args.output}")


def cmd_generate(args: argparse.Namespace) -> None:
    """Generate test data.

    Args:
        args: Command arguments
    """
    generator = TestDataGenerator(seed=args.seed)

    profiles = generator.bulk_generate(
        num_agents=args.agents,
        memories_per_agent=args.memories,
    )

    if args.output:
        import json
        with open(args.output, "w") as f:
            json.dump(profiles, f, indent=2)
        print(f"\n✅ Test data saved to: {args.output}")
    else:
        print(f"\n✅ Generated {len(profiles)} agent profiles")
        print(f"   Total memories: {len(profiles) * args.memories}")


def cmd_test(args: argparse.Namespace) -> None:
    """Run integration tests.

    Args:
        args: Command arguments
    """
    client = get_client()

    results = run_integration_test(client, agent_id=args.agent)

    if args.output:
        import json
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Test results saved to: {args.output}")

    # Exit with error code if tests failed
    if results["failed"] > 0:
        sys.exit(1)


def cmd_load_test(args: argparse.Namespace) -> None:
    """Load test data into Kyros.

    Args:
        args: Command arguments
    """
    client = get_client()

    load_test_data(
        client,
        num_agents=args.agents,
        memories_per_agent=args.memories,
    )


def cmd_profile(args: argparse.Namespace) -> None:
    """Profile Kyros operations.

    Args:
        args: Command arguments
    """
    client = get_client()

    with PerformanceProfiler() as profiler:
        # Run some operations
        print("Running profiled operations...")

        # Store a memory
        import time
        start = time.time()
        client.remember(
            agent_id=args.agent,
            content="Profile test memory",
            importance=0.7,
        )
        profiler.record_operation("store_memory", time.time() - start)
        profiler.record_api_call()

        # Recall memories
        start = time.time()
        client.recall(agent_id=args.agent, query="test", k=5)
        profiler.record_operation("recall_memories", time.time() - start)
        profiler.record_api_call()

    if args.output:
        import json
        report = profiler.get_report()
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n✅ Profile saved to: {args.output}")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Kyros CLI - Debug and test your Kyros deployment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Inspect command
    inspect_parser = subparsers.add_parser(
        "inspect",
        help="Inspect agent memories",
    )
    inspect_parser.add_argument("agent_id", help="Agent ID to inspect")
    inspect_parser.add_argument(
        "--detailed",
        action="store_true",
        help="Include detailed analysis",
    )
    inspect_parser.add_argument(
        "-o", "--output",
        help="Save report to file (JSON)",
    )

    # Compare command
    compare_parser = subparsers.add_parser(
        "compare",
        help="Compare multiple agents",
    )
    compare_parser.add_argument(
        "agent_ids",
        nargs="+",
        help="Agent IDs to compare",
    )
    compare_parser.add_argument(
        "-o", "--output",
        help="Save comparison to file (JSON)",
    )

    # Generate command
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate test data",
    )
    generate_parser.add_argument(
        "--agents",
        type=int,
        default=10,
        help="Number of agents to generate (default: 10)",
    )
    generate_parser.add_argument(
        "--memories",
        type=int,
        default=20,
        help="Memories per agent (default: 20)",
    )
    generate_parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducibility",
    )
    generate_parser.add_argument(
        "-o", "--output",
        help="Save test data to file (JSON)",
    )

    # Test command
    test_parser = subparsers.add_parser(
        "test",
        help="Run integration tests",
    )
    test_parser.add_argument(
        "--agent",
        default="test-integration",
        help="Agent ID for testing (default: test-integration)",
    )
    test_parser.add_argument(
        "-o", "--output",
        help="Save test results to file (JSON)",
    )

    # Load-test command
    load_test_parser = subparsers.add_parser(
        "load-test",
        help="Load test data into Kyros",
    )
    load_test_parser.add_argument(
        "--agents",
        type=int,
        default=5,
        help="Number of agents (default: 5)",
    )
    load_test_parser.add_argument(
        "--memories",
        type=int,
        default=10,
        help="Memories per agent (default: 10)",
    )

    # Profile command
    profile_parser = subparsers.add_parser(
        "profile",
        help="Profile Kyros operations",
    )
    profile_parser.add_argument(
        "--agent",
        default="profile-test",
        help="Agent ID for profiling (default: profile-test)",
    )
    profile_parser.add_argument(
        "-o", "--output",
        help="Save profile to file (JSON)",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Route to command handler
    commands = {
        "inspect": cmd_inspect,
        "compare": cmd_compare,
        "generate": cmd_generate,
        "test": cmd_test,
        "load-test": cmd_load_test,
        "profile": cmd_profile,
    }

    try:
        commands[args.command](args)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if os.getenv("DEBUG"):
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
