import asyncio
import os
import sys
from dotenv import load_dotenv

# Add vibetest-use to path if needed (though it was installed with -e)
# sys.path.append(os.path.abspath("vibetest-use"))

from vibetest.agents import run_pool, summarize_bug_reports, _test_results

async def main():
    load_dotenv()
    url = "http://localhost:5173"
    print(f"🚀 Starting Vibetest on {url}...")
    
    # Run only 1 agent to avoid Gemini free tier rate limits
    test_id = await run_pool(url, num_agents=1, headless=True)
    print(f"✅ Test swarm finished. ID: {test_id}")
    
    # Wait a bit for agents to conclude
    await asyncio.sleep(2)
    
    # Generate summary
    summary = await summarize_bug_reports(test_id)
    
    print("\n--- TEST SUMMARY ---")
    print(f"Status: {summary.get('status_emoji', '')} {summary.get('overall_status', 'N/A')}")
    print(f"Description: {summary.get('status_description', 'N/A')}")
    print(f"Total Issues: {summary.get('total_issues', 0)}")
    
    if "severity_breakdown" in summary:
        # ... existing print ...
        pass

    print("\n--- DETAILED FINDINGS ---")
    full_data = _test_results.get(test_id, {})
    for result in full_data.get("results", []):
         target = result.get('task', '')
         # Clean task a bit for display
         task_short = (target[:75] + '...') if len(target) > 75 else target
         print(f"\n🤖 Agent {result.get('agent_id')} | Task: {task_short}")
         if result.get("status") == "success":
             print(f"✅ Result: {result.get('result')}")
         else:
             print(f"❌ Error: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
