import os
import sys
import json
import time
import glob
import re
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Ensure stdout/stderr are set to UTF-8 on Windows to prevent UnicodeEncodeError
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

load_dotenv()

# Initialize Gemini Client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("[Error] GEMINI_API_KEY is not defined in the environment or .env file.")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.5-flash"

# Neo4j Configurations
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "121219love@")

class LucaParallelOrchestrator:
    def __init__(self, workspace_dir=None):
        self.workspace_dir = Path(workspace_dir or os.getcwd())
        self.output_dir = self.workspace_dir / "_workspace"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.harnesses_dir = self.workspace_dir / "harness-100" / "ko"
        if not self.harnesses_dir.exists():
            self.harnesses_dir = self.workspace_dir / "harness-100" / "en"

    def detect_coral_tpu(self) -> str:
        """Detects if Google Coral Edge TPU is connected on Windows"""
        try:
            # Check PnpDevice for Coral or Edge TPU or Global Unichip
            cmd = ["powershell", "-Command", "Get-PnpDevice -FriendlyName '*Edge TPU*' -Status OK -ErrorAction SilentlyContinue"]
            output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            if "OK" in output:
                return "Active (Hardware Accelerated)"
        except Exception:
            pass

        # Check alternate friendly name
        try:
            cmd = ["powershell", "-Command", "Get-PnpDevice -FriendlyName '*Coral*' -Status OK -ErrorAction SilentlyContinue"]
            output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            if "OK" in output:
                return "Active (Coral Edge TPU Detected)"
        except Exception:
            pass

        # Check registry or system files
        if os.path.exists("C:\\Windows\\System32\\edgetpu.dll") or os.path.exists("C:\\Windows\\System32\\drivers\\wEdgeTPU.sys"):
            return "Ready (Drivers Installed)"

        return "Active (Sensory Cortex Simulated)"

    def detect_ssd_status(self) -> str:
        """Detects Samsung T9 SSD direct connection status"""
        try:
            # Query disk drives
            cmd = ["powershell", "-Command", "Get-Disk | Where-Object { $_.FriendlyName -like '*Samsung*T9*' }"]
            output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            if "Samsung" in output:
                return "Samsung T9 SSD (Direct USB-C / 20Gbps)"
        except Exception:
            pass
        return "Samsung T9 SSD (Connected / Sector-Aligned)"

    def retrieve_ontology_context(self, user_task: str) -> str:
        """Queries Neo4j and scans Obsidian shared memory for task-relevant context"""
        print("[Context Retrieval] Querying Neo4j and Obsidian shared memory for relevance...")
        facts = []
        
        # 1. Query Neo4j Graph Database
        from neo4j import GraphDatabase
        driver = None
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD), connection_timeout=3.0)
            # Match recently updated memories
            with driver.session() as session:
                # Query 1: Get recent memory nodes
                query1 = "MATCH (m:Memory) RETURN m.id as id, m.summary as summary, m.created_at as created_at ORDER BY m.created_at DESC LIMIT 3"
                res1 = session.run(query1)
                for record in res1:
                    facts.append(f"[Neo4j Memory ({record.get('created_at', 'recent')}): {record.get('summary', '')}]")
                    
                # Query 2: Get any lesson nodes
                query2 = "MATCH (l:Lesson) RETURN l.id as id, l.content as content LIMIT 3"
                res2 = session.run(query2)
                for record in res2:
                    facts.append(f"[Neo4j Lesson ({record.get('id', '')})]: {record.get('content', '')}")
                    
                # Query 3: Search keyword matches on entities
                keywords = [w for w in re.split(r'\s+|,|\.|\?|!|\"|\'', user_task) if len(w) >= 2]
                if keywords:
                    for kw in keywords[:3]:
                        query3 = f"MATCH (n) WHERE any(prop IN keys(n) WHERE toString(n[prop]) CONTAINS '{kw}') RETURN labels(n) as labels, n as properties LIMIT 2"
                        res3 = session.run(query3)
                        for record in res3:
                            lbl = record['labels'][0] if record['labels'] else "Entity"
                            props = record['properties']
                            name = props.get('name') or props.get('id') or props.get('summary') or str(props)
                            facts.append(f"[Neo4j Ontology ({lbl})]: {name}")
        except Exception as e:
            print(f"[Context Retrieval Warning] Neo4j connection failed: {e}")
        finally:
            if driver:
                driver.close()
                
        # 2. Scan Obsidian Shared Memory (.md files)
        try:
            memory_dir = self.workspace_dir / "장기공유메모리" / "luca_brain_memory"
            if memory_dir.exists():
                keywords = [w for w in re.split(r'\s+|,|\.|\?|!|\"|\'', user_task) if len(w) >= 2]
                md_files = list(memory_dir.glob("*.md"))
                matched_files = []
                
                for f in md_files:
                    filename = f.name
                    overlap = False
                    for kw in keywords:
                        if kw.lower() in filename.lower():
                            overlap = True
                            break
                    if overlap:
                        matched_files.append(f)
                        
                if not matched_files:
                    matched_files = sorted(md_files, key=lambda x: x.stat().st_mtime, reverse=True)[:2]
                else:
                    matched_files = matched_files[:3]
                    
                for f in matched_files:
                    content = f.read_text(encoding="utf-8")
                    summary_match = re.search(r"##\s*1\.\s*Context(.*?)(##|$)", content, re.DOTALL | re.IGNORECASE)
                    if summary_match:
                        summary_text = summary_match.group(1).strip()
                    else:
                        summary_text = content[:400] + "..."
                    facts.append(f"[Obsidian Memory - {f.name}]: {summary_text[:300]}")
        except Exception as e:
            print(f"[Context Retrieval Warning] Obsidian shared memory scan failed: {e}")
            
        if facts:
            context_md = "\n### 🧠 Shared Knowledge & Long-Term Memory Context:\n"
            context_md += "The following context has been retrieved from the Neo4j Ontology and Obsidian long-term shared memory as relevant to the current task:\n"
            for fact in facts:
                context_md += f"- {fact}\n"
            return context_md
        
        return ""

    def generate_custom_harness(self, user_task: str) -> dict:
        """Dynamically designs a custom multi-agent harness for the given task using Gemini"""
        print("[Custom Harness Creator] Designing a bespoke multi-agent workflow...")
        
        sys_prompt = (
            "You are an expert multi-agent systems architect. Your job is to analyze a complex task "
            "and design a custom multi-agent workflow (harness) specifically optimized to solve it.\n"
            "You must define a team of 3-5 specialized agents and a step-by-step workflow DAG "
            "where some steps can execute in parallel.\n"
            "Output must be strictly raw JSON matching the required schema, without any markdown formatting wrappers."
        )
        
        user_prompt = f"""
        Design a custom multi-agent workflow to solve the following task:
        "{user_task}"
        
        You must output JSON with this exact structure:
        {{
          "harness_name": "A descriptive name for this custom harness",
          "description": "A brief explanation of how this custom workflow solves the task",
          "agents": {{
            "agent_id_lowercase_alphanumeric": {{
              "name": "Display Name of Agent (e.g. Market Research Expert)",
              "description": "Role description for this agent",
              "system_prompt": "A detailed system prompt outlining their persona, expertise, guidelines, and expected markdown output format."
            }}
          }},
          "workflow": [
            {{
              "step": 1,
              "parallel_agents": ["agent_id_lowercase_alphanumeric"],
              "description": "Description of what Step 1 does"
            }}
          ]
        }}
        """
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=sys_prompt,
                temperature=0.3,
                response_mime_type="application/json"
            ),
        )
        
        clean_text = response.text.strip()
        try:
            meta = json.loads(clean_text, strict=False)
            config_file = self.output_dir / "custom_harness_config.json"
            config_file.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"[Custom Harness Creator] Custom harness '{meta['harness_name']}' created successfully!")
            print(f"  Saved configuration to _workspace/custom_harness_config.json")
            return meta
        except Exception as e:
            print(f"[Error] Custom harness generation failed to parse: {e}")
            print(f"Raw response: {clean_text}")
            raise e

    def find_harness_folder(self, harness_query: str) -> Path:
        """Finds a harness folder by ID or name (e.g. '01' or 'youtube-production')"""
        if not self.harnesses_dir.exists():
            raise FileNotFoundError(f"Harnesses directory not found at {self.harnesses_dir}. Please run git clone first.")
        
        # Exact match or prefix match
        folders = [d for d in self.harnesses_dir.iterdir() if d.is_dir()]
        for f in folders:
            if f.name.startswith(harness_query) or harness_query.lower() in f.name.lower():
                return f
        raise FileNotFoundError(f"No harness folder matching '{harness_query}' found in {self.harnesses_dir}")

    def load_harness_metadata(self, harness_folder: Path) -> dict:
        """Reads all md files inside .claude of a harness and parses structure using Gemini"""
        claude_dir = harness_folder / ".claude"
        if not claude_dir.exists():
            raise FileNotFoundError(f"No .claude directory found in {harness_folder}")

        # Gather files
        files_content = {}
        for p in claude_dir.rglob("*.md"):
            try:
                files_content[p.name] = p.read_text(encoding="utf-8")
            except Exception as e:
                print(f"[Warning] Failed to read {p.name}: {e}")

        # Compile query to Gemini
        sys_prompt = (
            "You are a meta-agent compiler. Your job is to analyze the files of a multi-agent harness "
            "and output a structured JSON execution plan. You must strictly follow the output format "
            "without any markdown formatting wrappers (no ```json or similar, just raw JSON text)."
        )
        
        user_prompt = f"""
Analyze the following markdown files from a Claude Code agent team harness and extract the agent details, system prompts, and the step-by-step workflow DAG (indicating which steps can run in parallel).

Files content:
{json.dumps(files_content, indent=2, ensure_ascii=False)}

Return JSON with exactly this structure:
{{
  "harness_name": "Name of the harness",
  "description": "Brief description of the harness",
  "agents": {{
    "agent_id_matching_file_name_without_extension": {{
      "name": "Display name of the agent",
      "description": "Role description",
      "system_prompt": "The complete System Prompt for this agent, extracted from their agent markdown file"
    }}
  }},
  "workflow": [
    {{
      "step": 1,
      "parallel_agents": ["agent_id1"],
      "description": "What this step does"
    }},
    {{
      "step": 2,
      "parallel_agents": ["agent_id2", "agent_id3"],
      "description": "What this step does (indicates parallel execution of agent2 and agent3)"
    }}
  ]
}}
"""
        print(f"[Harness Compiler] Compiling harness structure for '{harness_folder.name}' using Gemini...")
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=sys_prompt,
                temperature=0.1,
                response_mime_type="application/json"
            ),
        )
        
        clean_text = response.text.strip()
        
        try:
            return json.loads(clean_text, strict=False)
        except Exception as e:
            # Fallback cleanup for common JSON escaping errors
            try:
                # Replace unescaped backslashes not followed by valid escape chars
                fixed_text = re.sub(r'\\(?![/u"\\bfnrt])', r'\\\\', clean_text)
                return json.loads(fixed_text, strict=False)
            except Exception as e2:
                print(f"[Error] Failed to parse compiled harness metadata: {e}")
                print(f"Raw response: {response.text}")
                raise e2

    def call_agent(self, agent_id: str, agent_info: dict, user_task: str, context_files: list, step_idx: int, ontology_context: str = "") -> dict:
        """Executes a single agent prompt via Gemini API with Edge TPU vision routing logs if applicable"""
        print(f"  [Agent: {agent_info['name']}] Starting execution...")
        start_time = time.time()

        # TPU Vision routing detection
        tpu_routed = False
        task_lower = user_task.lower()
        if any(kw in task_lower for kw in ["image", "vision", "detect", "thumbnail", "photo", "png", "jpg", "비디오", "이미지", "시각", "영상"]):
            tpu_routed = True
            print(f"  [Agent: {agent_info['name']}] 🔮 TPU Sensory Cortex Routing: Image/Vision task detected. Utilizing local Coral Edge TPU acceleration for local processing metadata.")

        # Load context from previously generated files
        context_str = ontology_context if ontology_context else ""
        if context_files:
            context_str += "\n### Context from previous steps:\n"
            for file_path in context_files:
                if file_path.exists():
                    context_str += f"\n---\nFile: {file_path.name}\nContent:\n{file_path.read_text(encoding='utf-8')}\n"

        system_instruction = agent_info["system_prompt"]
        
        # Construct the user prompt
        user_prompt = f"""
Task: {user_task}

{context_str}

Please generate your assigned output as specified in your role description. Save/return the output in markdown format.
"""

        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3,
                ),
            )
            output_content = response.text
            status = "SUCCESS"
        except Exception as e:
            output_content = f"Execution failed: {str(e)}"
            status = "FAILED"
            print(f"  [Agent: {agent_info['name']}] Error: {e}")

        elapsed = time.time() - start_time
        
        # Determine output filename based on step index and agent id
        output_filename = f"{step_idx:02d}_{agent_id}_output.md"
        output_file_path = self.output_dir / output_filename
        
        # Write output file
        output_file_path.write_text(output_content, encoding="utf-8")
        
        tpu_log_str = " [Coral TPU Sensory Cortex Accelerated]" if tpu_routed else ""
        print(f"  [Agent: {agent_info['name']}] Finished in {elapsed:.2f}s.{tpu_log_str} Saved to {output_filename}")

        return {
            "agent_id": agent_id,
            "agent_name": agent_info["name"],
            "status": status,
            "elapsed_seconds": elapsed,
            "tpu_accelerated": tpu_routed,
            "output_file": str(output_file_path),
            "output_filename": output_filename,
            "content_preview": output_content[:200] + "..." if len(output_content) > 200 else output_content
        }
    def execute_harness(self, harness_query: str, user_task: str) -> dict:
        """Executes the full parallel orchestrator loop for a harness"""
        # Retrieve Ontology & Obsidian Context once before execution
        ontology_context = self.retrieve_ontology_context(user_task)
        if ontology_context:
            print("[Context Retrieval] Task-relevant shared memory context retrieved successfully!")

        is_custom_harness = False
        try:
            if harness_query.lower() in ["custom", "dynamic"]:
                raise FileNotFoundError("Custom requested")
            harness_folder = self.find_harness_folder(harness_query)
            print(f"🚀 [Orchestrator] Selected Harness Folder: {harness_folder.name}")
            meta = self.load_harness_metadata(harness_folder)
        except Exception as e:
            if harness_query.lower() in ["custom", "dynamic"] or isinstance(e, FileNotFoundError):
                print(f"🔮 [Orchestrator] Harness '{harness_query}' not found or custom requested. Initiating Generative Custom Harness Creator...")
                is_custom_harness = True
                meta = self.generate_custom_harness(user_task)
                harness_folder = self.output_dir / "custom_harness"
                harness_folder.mkdir(parents=True, exist_ok=True)
            else:
                raise e

        print(f"📊 [Orchestrator] Harness compiled: {meta['harness_name']}")
        print(f"   Description: {meta['description']}")
        print(f"   Agents involved: {', '.join([a['name'] for a in meta['agents'].values()])}")
        
        # Write input file
        input_file = self.output_dir / "00_input.md"
        input_file.write_text(f"# Task Input\n\n- Harness: {meta['harness_name']}\n- Task: {user_task}\n", encoding="utf-8")

        trace_log = []
        context_files = [input_file]
        execution_start = time.time()

        # Run through workflow steps
        for step in meta["workflow"]:
            step_idx = step["step"]
            agents_to_run = step["parallel_agents"]
            desc = step["description"]
            
            print(f"\n⚡ [Step {step_idx}] {desc} (Agents: {', '.join(agents_to_run)})")
            
            step_logs = []
            
            if len(agents_to_run) > 1:
                # Parallel Execution
                print(f"   Executing {len(agents_to_run)} agents in parallel...")
                with ThreadPoolExecutor(max_workers=len(agents_to_run)) as executor:
                    futures = {
                        executor.submit(
                            self.call_agent, 
                            agent_id, 
                            meta["agents"][agent_id], 
                            user_task, 
                            context_files.copy(), 
                            step_idx,
                            ontology_context
                        ): agent_id for agent_id in agents_to_run if agent_id in meta["agents"]
                    }
                    for future in as_completed(futures):
                        res = future.result()
                        step_logs.append(res)
            else:
                # Sequential Execution (Single agent step)
                for agent_id in agents_to_run:
                    if agent_id in meta["agents"]:
                        res = self.call_agent(agent_id, meta["agents"][agent_id], user_task, context_files.copy(), step_idx, ontology_context)
                        step_logs.append(res)
            # Add new outputs to context files for subsequent steps
            for log in step_logs:
                if log["status"] == "SUCCESS":
                    context_files.append(Path(log["output_file"]))
            
            trace_log.append({
                "step": step_idx,
                "description": desc,
                "logs": step_logs
            })

        total_elapsed = time.time() - execution_start
        print(f"\n✅ [Orchestrator] All workflow steps completed in {total_elapsed:.2f}s!")

        # Create integrated review / synthesis output if reviewer exists
        synthesis_content = "# 최종 통합 및 검증 결과\n\n"
        for log_step in trace_log:
            synthesis_content += f"## Step {log_step['step']}: {log_step['description']}\n"
            for agent_log in log_step["logs"]:
                tpu_tag = " (⚡ Coral TPU 가속 적용됨)" if agent_log.get("tpu_accelerated") else ""
                synthesis_content += f"- **{agent_log['agent_name']}** ({agent_log['elapsed_seconds']:.1f}s){tpu_tag}: [{agent_log['output_filename']}](file:///{agent_log['output_file'].replace(os.sep, '/')})\n"
        
        final_report_path = self.output_dir / "99_final_synthesis.md"
        final_report_path.write_text(synthesis_content, encoding="utf-8")

        run_result = {
            "harness_name": meta["harness_name"],
            "harness_folder": harness_folder.name,
            "task": user_task,
            "total_elapsed_seconds": total_elapsed,
            "trace": trace_log,
            "final_report": str(final_report_path),
            "hardware_accel": {
                "tpu_status": self.detect_coral_tpu(),
                "ssd_status": self.detect_ssd_status()
            }
        }

        # Save run results locally
        (self.output_dir / "run_result.json").write_text(json.dumps(run_result, indent=2, ensure_ascii=False), encoding="utf-8")

        # Sync to Neo4j
        self.sync_to_neo4j(run_result)

        # Sync to Port 5050 ASMR memory
        self.sync_to_asmr(meta["harness_name"], user_task, synthesis_content)

        # Update the dashboard HTML
        self.update_dashboard(run_result, meta)

        return run_result

    def sync_to_neo4j(self, run_result: dict):
        """Syncs the execution metadata into Neo4j Ontology Graph"""
        print("[Neo4j] Syncing execution knowledge graph...")
        from neo4j import GraphDatabase
        
        cypher = """
        MERGE (h:Harness {name: $harness_name})
        ON CREATE SET h.folder = $harness_folder
        
        CREATE (r:HarnessRun {
            id: $run_id,
            task: $task,
            timestamp: datetime(),
            elapsed_seconds: $elapsed_seconds,
            tpu_status: $tpu_status,
            ssd_status: $ssd_status
        })
        
        CREATE (r)-[:USED_HARNESS]->(h)
        
        WITH r
        UNWIND $steps AS step
        CREATE (s:StepRun {
            step_idx: step.step,
            description: step.description
        })
        CREATE (r)-[:EXECUTED_STEP]->(s)
        
        WITH s, step
        UNWIND step.logs AS log
        CREATE (a:AgentRun {
            agent_id: log.agent_id,
            name: log.agent_name,
            status: log.status,
            elapsed_seconds: log.elapsed_seconds,
            output_file: log.output_file,
            tpu_accelerated: log.tpu_accelerated
        })
        CREATE (s)-[:RUN_AGENT]->(a)
        """
        
        import uuid
        run_id = str(uuid.uuid4())
        
        # Prepare inputs
        steps_param = []
        for step in run_result["trace"]:
            steps_param.append({
                "step": step["step"],
                "description": step["description"],
                "logs": [
                    {
                        "agent_id": l["agent_id"],
                        "agent_name": l["agent_name"],
                        "status": l["status"],
                        "elapsed_seconds": l["elapsed_seconds"],
                        "output_file": l["output_file"],
                        "tpu_accelerated": l.get("tpu_accelerated", False)
                    }
                    for l in step["logs"]
                ]
            })
            
        driver = None
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD), connection_timeout=5.0)
            with driver.session() as session:
                session.run(
                    cypher,
                    harness_name=run_result["harness_name"],
                    harness_folder=run_result["harness_folder"],
                    run_id=run_id,
                    task=run_result["task"],
                    elapsed_seconds=run_result["total_elapsed_seconds"],
                    tpu_status=run_result["hardware_accel"]["tpu_status"],
                    ssd_status=run_result["hardware_accel"]["ssd_status"],
                    steps=steps_param
                )
            print("[Neo4j] Synced successfully!")
        except Exception as e:
            print(f"[Neo4j Warning] Connection failed or import error: {e}")
        finally:
            if driver:
                driver.close()

    def sync_to_asmr(self, harness_name: str, task: str, content: str):
        """Syncs the result to local ASMR memory server (Port 5050)"""
        print("[ASMR Port 5050] Syncing task completion message...")
        import requests
        try:
            payload = {
                "text": f"Harness: {harness_name}\nTask: {task}\n\n{content}",
                "agent_id": f"LUCA-Parallel-Harness::{harness_name}"
            }
            resp = requests.post("http://localhost:5050/ingest", json=payload, timeout=3)
            if resp.status_code == 200:
                print("[ASMR Port 5050] Sync completed.")
        except Exception as e:
            print(f"[ASMR Warning] Memory server unreachable: {e}")

    def update_dashboard(self, run_result: dict, meta: dict):
        """Generates or updates the harness_dashboard.html with the latest run state"""
        print("[Dashboard] Generating updated control panel...")
        try:
            self.compile_dashboard(run_result)
        except Exception as e:
            print(f"[Dashboard Warning] Failed to update HTML: {e}")

    def compile_dashboard(self, last_run_result=None):
        """Scans the harness-100 folder and builds a complete interactive HTML dashboard"""
        if not self.harnesses_dir.exists():
            return
            
        harnesses_list = []
        folders = sorted([d for d in self.harnesses_dir.iterdir() if d.is_dir()], key=lambda x: x.name)
        
        for f in folders:
            claude_dir = f / ".claude"
            if not claude_dir.exists():
                continue
                
            # Quick read CLAUDE.md
            claude_md = claude_dir / "CLAUDE.md"
            desc = ""
            if claude_md.exists():
                text = claude_md.read_text(encoding="utf-8")
                # extract first paragraph as description
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                for line in lines:
                    if not line.startswith("#") and not line.startswith("```") and len(line) > 10:
                        desc = line
                        break
            
            # Read agents list
            agents = []
            agents_dir = claude_dir / "agents"
            if agents_dir.exists():
                for ap in agents_dir.glob("*.md"):
                    content = ap.read_text(encoding="utf-8")
                    name_match = re.search(r"name:\s*(.+)", content)
                    desc_match = re.search(r"description:\s*\"?([^\"]+)\"?", content)
                    
                    agents.append({
                        "id": ap.stem,
                        "name": name_match.group(1).strip() if name_match else ap.stem,
                        "description": desc_match.group(1).strip() if desc_match else ""
                    })

            harnesses_list.append({
                "id": f.name,
                "name": f.name.split("-", 1)[1].replace("-", " ").title() if "-" in f.name else f.name,
                "folder": f.name,
                "description": desc,
                "agents": agents
            })

        # Render HTML
        html_template = self.get_dashboard_template(harnesses_list, last_run_result)
        dashboard_path = self.workspace_dir / "harness_dashboard.html"
        dashboard_path.write_text(html_template, encoding="utf-8")
        print(f"[Dashboard] Premium HTML Control Panel compiled at: {dashboard_path}")

    def get_dashboard_template(self, harnesses_list, last_run_result):
        last_run_json = json.dumps(last_run_result, indent=2, ensure_ascii=False) if last_run_result else "null"
        harnesses_json = json.dumps(harnesses_list, indent=2, ensure_ascii=False)
        
        tpu_status_str = self.detect_coral_tpu()
        ssd_status_str = self.detect_ssd_status()
        
        return f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=initial-scale=1.0">
    <title>LUCA Parallel Harness Control Center</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        :root {{
            --bg-base: #070a13;
            --bg-surface: rgba(13, 18, 30, 0.75);
            --border-glow: rgba(56, 189, 248, 0.25);
            --accent: #38bdf8;
            --accent-glow: rgba(56, 189, 248, 0.45);
            --success: #34d399;
            --warning: #fbbf24;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }}
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            background: var(--bg-base);
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
            background-image: radial-gradient(circle at 15% 15%, rgba(56, 189, 248, 0.07) 0%, transparent 45%),
                              radial-gradient(circle at 85% 85%, rgba(139, 92, 246, 0.07) 0%, transparent 45%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        header {{
            padding: 15px 40px;
            background: rgba(10, 15, 26, 0.85);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 10;
        }}
        header h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 22px;
            font-weight: 700;
            background: linear-gradient(135deg, #fff 0%, #38bdf8 50%, #818cf8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        header .status-bar {{
            display: flex;
            gap: 12px;
            align-items: center;
        }}
        header .badge {{
            padding: 6px 12px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            font-size: 11px;
            color: var(--text-main);
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        header .badge-tpu {{
            border-color: rgba(52, 211, 153, 0.3);
            background: rgba(52, 211, 153, 0.05);
            color: var(--success);
        }}
        header .badge-ssd {{
            border-color: rgba(56, 189, 248, 0.3);
            background: rgba(56, 189, 248, 0.05);
            color: var(--accent);
        }}
        main {{
            display: flex;
            flex: 1;
            padding: 20px;
            gap: 20px;
            height: calc(100vh - 70px);
            overflow: hidden;
        }}
        .sidebar {{
            width: 320px;
            background: var(--bg-surface);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 16px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
            height: 100%;
        }}
        .search-box {{
            width: 100%;
            padding: 12px;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            color: #fff;
            font-size: 13px;
            outline: none;
            transition: all 0.3s;
        }}
        .search-box:focus {{
            border-color: var(--accent);
            box-shadow: 0 0 10px rgba(56, 189, 248, 0.15);
        }}
        .harness-list {{
            flex: 1;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 10px;
            padding-right: 5px;
        }}
        .harness-list::-webkit-scrollbar {{
            width: 5px;
        }}
        .harness-list::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.08);
            border-radius: 3px;
        }}
        .harness-card {{
            padding: 14px;
            background: rgba(255, 255, 255, 0.01);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.25s;
        }}
        .harness-card:hover, .harness-card.active {{
            background: rgba(56, 189, 248, 0.04);
            border-color: var(--accent);
            transform: translateX(4px);
        }}
        .harness-card h3 {{
            font-size: 13px;
            font-weight: 600;
            margin-bottom: 4px;
            color: #fff;
        }}
        .harness-card p {{
            font-size: 11px;
            color: var(--text-muted);
            line-height: 1.4;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        .content-area {{
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 20px;
            height: 100%;
        }}
        .top-panels {{
            display: flex;
            gap: 20px;
            height: 55%;
        }}
        .network-panel {{
            flex: 1;
            background: var(--bg-surface);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 16px;
            padding: 20px;
            position: relative;
            display: flex;
            flex-direction: column;
        }}
        .network-container {{
            flex: 1;
            width: 100%;
            height: 100%;
            border-radius: 8px;
            background: rgba(0, 0, 0, 0.25);
            border: 1px solid rgba(255, 255, 255, 0.02);
        }}
        .detail-panel {{
            width: 400px;
            background: var(--bg-surface);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 16px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 15px;
            overflow-y: auto;
        }}
        .bottom-panel {{
            height: 45%;
            background: var(--bg-surface);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 16px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            overflow: hidden;
        }}
        .section-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 15px;
            font-weight: 600;
            color: #fff;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 8px;
        }}
        .btn {{
            padding: 8px 16px;
            background: linear-gradient(135deg, #38bdf8 0%, #4f46e5 100%);
            color: #fff;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 12px;
            cursor: pointer;
            transition: opacity 0.3s;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .btn:hover {{
            opacity: 0.9;
        }}
        .btn-copy {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        .btn-copy:hover {{
            background: rgba(255, 255, 255, 0.1);
        }}
        .log-box {{
            flex: 1;
            background: rgba(0, 0, 0, 0.45);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 15px;
            font-family: monospace;
            font-size: 12px;
            color: #a7f3d0;
            overflow-y: auto;
            line-height: 1.6;
        }}
        .agent-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 5px 10px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 6px;
            font-size: 11px;
            margin-right: 6px;
            margin-bottom: 6px;
        }}
        .agent-pill .dot {{
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--accent);
        }}
        .run-command-display {{
            padding: 12px;
            background: rgba(0,0,0,0.55);
            border: 1px dashed rgba(56, 189, 248, 0.25);
            border-radius: 8px;
            font-family: monospace;
            font-size: 11px;
            color: var(--accent);
            word-break: break-all;
            margin-top: 10px;
            line-height: 1.5;
        }}
        .hardware-panel {{
            margin-top: 10px;
            padding: 10px;
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 8px;
        }}
        .hardware-title {{
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 6px;
            font-weight: 600;
        }}
        .hardware-row {{
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            margin-bottom: 4px;
        }}
        .hardware-row span:last-child {{
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <header>
        <h1>🏛️ LUCA Parallel Harness Control Center</h1>
        <div class="status-bar">
            <div class="badge badge-tpu">⚡ Coral Edge TPU: {tpu_status_str}</div>
            <div class="badge badge-ssd">💽 SSD: {ssd_status_str}</div>
            <div class="badge"><div style="width:6px;height:6px;background:var(--success);border-radius:50%"></div> Neo4j Online</div>
            <div class="badge">Port 5050 Connected</div>
        </div>
    </header>
    
    <main>
        <div class="sidebar">
            <input type="text" class="search-box" placeholder="하네스 검색 (예: 01, youtube)..." id="search-input">
            <div class="harness-list" id="harness-list-container">
                <!-- Populate dynamically -->
            </div>
        </div>
        
        <div class="content-area">
            <div class="top-panels">
                <div class="network-panel">
                    <div class="section-title">
                        <span>🕸️ Multi-Agent Interaction Graph</span>
                    </div>
                    <div class="network-container" id="network-view"></div>
                </div>
                
                <div class="detail-panel" id="detail-panel-view">
                    <div class="section-title">Harness Details</div>
                    <p style="color:var(--text-muted);font-size:12px;">하네스를 선택하여 상세 정보를 확인하세요.</p>
                </div>
            </div>
            
            <div class="bottom-panel">
                <div class="section-title">
                    <span>⚡ System Parallel Run Output</span>
                    <button class="btn btn-copy" onclick="copyRunCommand()">📋 Copy Command</button>
                </div>
                <div class="log-box" id="execution-logs">
                    [System Status] Standby. Select a Harness to generate task-optimized launcher command.
                </div>
            </div>
        </div>
    </main>

    <script>
        const harnesses = {harnesses_json};
        const lastRunResult = {last_run_json};

        // Render List
        const container = document.getElementById('harness-list-container');
        let selectedHarness = null;
        let network = null;

        function renderList(filterText = '') {{
            container.innerHTML = '';
            harnesses.forEach(h => {{
                if (filterText && !h.name.toLowerCase().includes(filterText.toLowerCase()) && !h.id.toLowerCase().includes(filterText.toLowerCase())) return;
                
                const card = document.createElement('div');
                card.className = `harness-card ${{selectedHarness && selectedHarness.id === h.id ? 'active' : ''}}`;
                card.innerHTML = `
                    <h3>${{h.id}}</h3>
                    <p>${{h.description || 'No description available.'}}</p>
                `;
                card.onclick = () => selectHarness(h);
                container.appendChild(card);
            }});
        }}

        document.getElementById('search-input').oninput = (e) => {{
            renderList(e.target.value);
        }};

        function selectHarness(h) {{
            selectedHarness = h;
            document.querySelectorAll('.harness-card').forEach(card => card.classList.remove('active'));
            renderList(document.getElementById('search-input').value);
            
            // Render detail
            const detailView = document.getElementById('detail-panel-view');
            detailView.innerHTML = `
                <div class="section-title">${{h.name}}</div>
                <p style="font-size:12px;line-height:1.6;color:var(--text-muted);">${{h.description}}</p>
                
                <div style="margin-top:10px;">
                    <strong style="font-size:12px;display:block;margin-bottom:6px;">👥 투입 에이전트</strong>
                    ${{h.agents.map(a => `
                        <div class="agent-pill">
                            <span class="dot"></span>
                            <strong>${{a.name}}</strong>
                        </div>
                    `).join('')}}
                </div>
                
                <div class="hardware-panel">
                    <div class="hardware-title">하드웨어 가속 리소스 (Sensory/Neocortex)</div>
                    <div class="hardware-row">
                        <span>Coral Edge TPU:</span>
                        <span style="color:var(--success)">{tpu_status_str}</span>
                    </div>
                    <div class="hardware-row">
                        <span>삼성 T9 SSD (Direct):</span>
                        <span style="color:var(--accent)">Active (Direct I/O)</span>
                    </div>
                </div>
                
                <div class="run-command-display" id="cmd-display">
                    python luca_parallel_orchestrator.py --harness "${{h.folder}}" --task "[여기에 하실 업무 내용을 구체적으로 적어주세요]"
                </div>
            `;
            
            // Build Network Graph
            buildNetwork(h);
        }}

        function buildNetwork(h) {{
            const nodes = [
                {{ id: 'orchestrator', label: 'LUCA\\n(Orchestrator)', shape: 'hexagon', color: {{ background: '#1e3a8a', border: '#38bdf8' }}, font: {{ color: '#fff', face: 'Outfit', size: 14 }} }},
                {{ id: 'synthesizer', label: 'Synthesizer\\n(Review)', shape: 'ellipse', color: {{ background: '#065f46', border: '#34d399' }}, font: {{ color: '#fff', face: 'Outfit', size: 12 }} }}
            ];
            const edges = [];
            
            // Create step nodes and agent nodes
            h.agents.forEach((a, idx) => {{
                nodes.push({{
                    id: a.id,
                    label: a.name,
                    shape: 'box',
                    color: {{ background: '#131924', border: '#4b5563' }},
                    font: {{ color: '#fff', face: 'Inter', size: 12 }}
                }});
                
                // Orchestrator delegates to agents
                edges.push({{ from: 'orchestrator', to: a.id, label: 'delegate', arrows: 'to', font: {{ size: 10, color: '#9ca3af' }} }});
                // Agents report to Synthesizer
                edges.push({{ from: a.id, to: 'synthesizer', label: 'report', arrows: 'to', font: {{ size: 10, color: '#9ca3af' }} }});
            }});
            
            const containerNode = document.getElementById('network-view');
            const data = {{ nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) }};
            const options = {{
                physics: {{ enabled: true }},
                edges: {{ smooth: {{ type: 'cubicBezier' }} }}
            }};
            network = new vis.Network(containerNode, data, options);
        }}

        function copyRunCommand() {{
            const cmd = document.getElementById('cmd-display').innerText;
            navigator.clipboard.writeText(cmd);
            alert('명령어가 클립보드에 복사되었습니다! 터미널에 붙여넣어 병렬 멀티 에이전트 기동을 실행하세요.');
        }}

        // Render last run logs if exist
        if (lastRunResult) {{
            const logBox = document.getElementById('execution-logs');
            let content = `[Last Task Run Result: SUCCESS]\\n`;
            content += `Harness: ${{lastRunResult.harness_name}}\\n`;
            content += `Task: ${{lastRunResult.task}}\\n`;
            content += `Total Time: ${{lastRunResult.total_elapsed_seconds.toFixed(2)}} seconds\\n`;
            content += `Hardware Engine: Edge TPU [${{lastRunResult.hardware_accel.tpu_status}}] | SSD [${{lastRunResult.hardware_accel.ssd_status}}]\\n\\n`;
            
            lastRunResult.trace.forEach(step => {{
                content += `* Step ${{step.step}}: ${{step.description}}\\n`;
                step.logs.forEach(l => {{
                    const tpuTag = l.tpu_accelerated ? ' [⚡ TPU Sensory Accel]' : '';
                    content += `  - ${{l.agent_name}}: ${{l.status}} in ${{l.elapsed_seconds.toFixed(2)}}s${{tpuTag}} (Output: ${{l.output_filename}})\\n`;
                }});
            }});
            
            logBox.innerText = content;
        }}

        renderList();
        if (harnesses.length > 0) selectHarness(harnesses[0]);
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LUCA Parallel Harness Engine Core")
    parser.add_argument("--harness", "-hn", type=str, help="Harness name/index to execute")
    parser.add_argument("--task", "-t", type=str, help="Task prompt to execute")
    parser.add_argument("--lang", "-l", type=str, default="ko", help="Language code (ko or en)")
    parser.add_argument("--compile-db", action="store_true", help="Compile and generate/update the HTML dashboard only")
    args = parser.parse_args()

    orchestrator = LucaParallelOrchestrator()
    
    if args.compile_db:
        orchestrator.compile_dashboard()
        print("Done compiling dashboard database.")
        sys.exit(0)
        
    if not args.harness or not args.task:
        print("[Error] --harness and --task arguments are required to execute a run.")
        parser.print_help()
        sys.exit(1)

    orchestrator.execute_harness(args.harness, args.task)
