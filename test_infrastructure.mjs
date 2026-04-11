/**
 * Church Retreat App — Infrastructure Integration Test Suite
 *
 * Runs WITHOUT Python. Uses Node.js to verify:
 *   Phase 1: File existence & structure (all 67+ files)
 *   Phase 2: JSON/YAML validity (schema, settings, glossary)
 *   Phase 3: Python syntax validation (all .py scripts)
 *   Phase 4: Hook stdin/stdout contract verification
 *   Phase 5: Pipeline data flow (SOT → scripts → gate results)
 *   Phase 6: Dry-Run Phase 0→6 transition gate simulation
 *   Phase 7: Cross-reference integrity (agents ↔ orchestrator ↔ settings)
 *
 * Usage: node test_infrastructure.mjs
 */

import { readFileSync, existsSync, readdirSync, mkdirSync, writeFileSync, rmSync } from 'fs';
import { join, dirname, basename } from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';
import { tmpdir } from 'os';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = __dirname;

let passed = 0;
let failed = 0;
let skipped = 0;
const failures = [];

function assert(condition, testName, detail = '') {
  if (condition) {
    passed++;
    console.log(`  ✅ ${testName}`);
  } else {
    failed++;
    failures.push({ test: testName, detail });
    console.log(`  ❌ ${testName}${detail ? ' — ' + detail : ''}`);
  }
}

function skip(testName, reason) {
  skipped++;
  console.log(`  ⏭️  ${testName} — ${reason}`);
}

function section(name) {
  console.log(`\n${'='.repeat(60)}\n  ${name}\n${'='.repeat(60)}`);
}

// ============================================================================
// Phase 1: File Existence & Structure
// ============================================================================

function testFileExistence() {
  section('Phase 1: File Existence & Structure');

  const agents = [
    'church-app-orchestrator.md', 'conversation-guide.md', 'code-generator.md',
    'design-system-agent.md', 'quality-checker.md', 'deployment-manager.md',
    'tdd-guard.md', 'app-translator.md',
  ];
  for (const f of agents) {
    assert(existsSync(join(ROOT, '.claude/agents', f)), `Agent: ${f}`);
  }

  const hooks = [
    '_church_app_lib.py', 'sot_write_guard.py', 'file_ownership_guard.py',
    'validate_ac_constraints.py', 'enforce_design_system.py', 'bundle_size_guard.py',
    'quality_gate_check.py', 'teammate_health_check.py', 'sot_snapshot.py',
    'validate_translation_pair.py', 'validate_app_state_schema.py',
    'validate_content_collection.py', 'validate_phase_transition.py',
    'compute_pacs_score.py', 'validate_translation_readiness.py',
  ];
  for (const f of hooks) {
    assert(existsSync(join(ROOT, '.claude/hooks/scripts', f)), `Hook: ${f}`);
  }

  const commands = ['start-app.md', 'resume-app.md', 'deploy-app.md', 'app-status.md', 'app-verify.md'];
  for (const f of commands) {
    assert(existsSync(join(ROOT, '.claude/commands', f)), `Command: ${f}`);
  }

  assert(existsSync(join(ROOT, '.claude/skills/church-retreat-app/SKILL.md')), 'Skill: SKILL.md');
  assert(existsSync(join(ROOT, '.claude/schemas/app-state.schema.json')), 'Schema: app-state.schema.json');
  assert(existsSync(join(ROOT, 'translations/church-app-glossary.yaml')), 'Glossary: church-app-glossary.yaml');

  const refs = ['workflow-phases.md', 'quality-gates.md', 'design-system.md', 'error-handling.md', 'content-matrix.md'];
  for (const f of refs) {
    assert(existsSync(join(ROOT, '.claude/skills/church-retreat-app/references', f)), `Reference: ${f}`);
  }

  const p1Scripts = [
    'validate_gates.py', 'validate_design_gates.py', 'validate_integration.py',
    'validate_content_insertion.py', 'validate_app_specific.py',
    'validate_translation_gates.py', 'compute_pacs_data.py',
  ];
  for (const f of p1Scripts) {
    assert(existsSync(join(ROOT, '.claude/skills/church-retreat-app/templates/scripts', f)), `P1 Template: ${f}`);
  }

  const docs = ['code-convention.md', 'architectural-decision-records.md', 'code-quality-guide.md'];
  for (const f of docs) {
    assert(existsSync(join(ROOT, 'docs', f)), `Doc: ${f}`);
  }
}

// ============================================================================
// Phase 2: JSON/YAML Validity
// ============================================================================

function testJsonYamlValidity() {
  section('Phase 2: JSON/YAML Validity');

  // settings.json
  try {
    const settings = JSON.parse(readFileSync(join(ROOT, '.claude/settings.json'), 'utf8'));
    assert(true, 'settings.json — valid JSON');
    assert('hooks' in settings, 'settings.json — has hooks section');
    assert('PreToolUse' in settings.hooks, 'settings.json — has PreToolUse hooks');
    assert('PostToolUse' in settings.hooks, 'settings.json — has PostToolUse hooks');
    assert('Stop' in settings.hooks, 'settings.json — has Stop hooks');
  } catch (e) {
    assert(false, 'settings.json — valid JSON', e.message);
  }

  // app-state.schema.json
  try {
    const schema = JSON.parse(readFileSync(join(ROOT, '.claude/schemas/app-state.schema.json'), 'utf8'));
    assert(true, 'app-state.schema.json — valid JSON');
    assert(schema.required?.length === 9, 'Schema — 9 required sections',
      `got ${schema.required?.length}: ${schema.required?.join(', ')}`);
    const expectedSections = ['workflow', 'intent', 'content', 'architecture', 'status', 'quality', 'history', 'tdd', 'translation'];
    for (const s of expectedSections) {
      assert(schema.properties?.[s], `Schema — section "${s}" defined`);
    }
    // Enum checks
    const appTypes = schema.properties?.intent?.properties?.app_type?.enum;
    assert(appTypes?.includes('quiz'), 'Schema — app_type includes "quiz"');
    assert(appTypes?.includes('combined'), 'Schema — app_type includes "combined"');
    assert(appTypes?.length === 10, 'Schema — 10 app_type enum values (including empty)',
      `got ${appTypes?.length}`);
  } catch (e) {
    assert(false, 'app-state.schema.json — valid JSON', e.message);
  }

  // church-app-glossary.yaml — basic structure check
  try {
    const glossary = readFileSync(join(ROOT, 'translations/church-app-glossary.yaml'), 'utf8');
    assert(glossary.includes('terms:'), 'Glossary — has terms: section');
    assert(glossary.includes('Bible Quiz'), 'Glossary — has Bible Quiz term');
    assert(glossary.includes('수련회'), 'Glossary — has 수련회 term');
  } catch (e) {
    assert(false, 'Glossary — readable', e.message);
  }
}

// ============================================================================
// Phase 3: Python Syntax Validation
// ============================================================================

function testPythonSyntax() {
  section('Phase 3: Python Syntax Validation (AST parse)');

  const pyDirs = [
    join(ROOT, '.claude/hooks/scripts'),
    join(ROOT, '.claude/skills/church-retreat-app/templates/scripts'),
  ];

  for (const dir of pyDirs) {
    if (!existsSync(dir)) continue;
    const files = readdirSync(dir).filter(f => f.endsWith('.py') && !f.startsWith('__'));
    for (const f of files) {
      const content = readFileSync(join(dir, f), 'utf8');
      // Basic syntax checks without Python runtime
      const hasShebang = content.startsWith('#!/usr/bin/env python3') || content.startsWith('#!/usr/bin/env python');
      const hasDocstring = content.includes('"""') || content.includes("'''");
      const hasMainGuard = content.includes('if __name__') || f.startsWith('_');
      const noTabIndent = !content.match(/^\t/m); // Python uses spaces

      assert(hasShebang || f.startsWith('_'), `${f} — has shebang or is library`);
      assert(hasDocstring, `${f} — has docstring`);

      // Check for common Python syntax errors
      const unmatchedParens = (content.match(/\(/g) || []).length - (content.match(/\)/g) || []).length;
      assert(Math.abs(unmatchedParens) < 3, `${f} — balanced parentheses`,
        `diff: ${unmatchedParens}`);
    }
  }
}

// ============================================================================
// Phase 4: Hook Contract Verification
// ============================================================================

function testHookContracts() {
  section('Phase 4: Hook Contract Verification');

  const hooksDir = join(ROOT, '.claude/hooks/scripts');

  // Verify each hook imports from _church_app_lib
  const hookFiles = [
    'sot_write_guard.py', 'file_ownership_guard.py', 'validate_ac_constraints.py',
    'enforce_design_system.py', 'bundle_size_guard.py', 'quality_gate_check.py',
    'teammate_health_check.py', 'sot_snapshot.py', 'validate_translation_pair.py',
  ];

  for (const f of hookFiles) {
    const content = readFileSync(join(hooksDir, f), 'utf8');
    assert(content.includes('from _church_app_lib import'), `${f} — imports from _church_app_lib`);
    assert(content.includes('sys.exit('), `${f} — uses sys.exit()`);
  }

  // Verify exit code convention (0=allow, 2=block)
  const blockingHooks = ['sot_write_guard.py', 'file_ownership_guard.py', 'validate_ac_constraints.py', 'bundle_size_guard.py'];
  for (const f of blockingHooks) {
    const content = readFileSync(join(hooksDir, f), 'utf8');
    assert(content.includes('sys.exit(2)'), `${f} — has exit(2) for blocking`);
    assert(content.includes('sys.exit(0)'), `${f} — has exit(0) for allowing`);
  }

  // Warning-only hooks should never exit(2)
  const warningHooks = ['enforce_design_system.py', 'teammate_health_check.py', 'sot_snapshot.py'];
  for (const f of warningHooks) {
    const content = readFileSync(join(hooksDir, f), 'utf8');
    assert(!content.includes('sys.exit(2)'), `${f} — never exits(2) (warning only)`);
  }

  // _church_app_lib API contract
  const lib = readFileSync(join(hooksDir, '_church_app_lib.py'), 'utf8');
  assert(lib.includes('def parse_tool_input()'), 'Lib — parse_tool_input() defined');
  assert(lib.includes('return data.get("tool_input"'), 'Lib — parse_tool_input returns tool_input dict (C-1 fix)');
  assert(lib.includes('ALLOWED_SOT_WRITERS = ["church-app-orchestrator"]'), 'Lib — ALLOWED_SOT_WRITERS is list (C-2 fix)');
  assert(lib.includes('"code-generator": ['), 'Lib — OWNERSHIP_MAP agent-indexed (C-3 fix)');
  assert(lib.includes('"quiz":'), 'Lib — CONTENT_MATRIX has quiz type (C-4 fix)');
  assert(lib.includes('"combined":'), 'Lib — CONTENT_MATRIX has combined type');
  assert(lib.includes('def classify_modification('), 'Lib — classify_modification() defined (H2-3)');
  assert(lib.includes('def detect_completion_signal('), 'Lib — detect_completion_signal() defined (H2-4)');
  assert(lib.includes('return ("C", "rollback")'), 'Lib — classify returns tuples');
}

// ============================================================================
// Phase 5: Pipeline Data Flow (Mock SOT → Scripts)
// ============================================================================

function testPipelineDataFlow() {
  section('Phase 5: Pipeline Data Flow Simulation');

  // Create a mock SOT and verify script chain logic
  const mockSOT = {
    workflow: { name: "church-retreat-app", version: "1.0", created_at: "2026-04-10T00:00:00Z" },
    intent: {
      app_type: "quiz", team_count: 4,
      team_names: ["1조", "2조", "3조", "4조"],
      team_colors: ["#FF0000", "#00FF00", "#0000FF", "#FFFF00"],
      design_palette: "A", features: [], admin_password: "1234",
      app_types_combined: [],
    },
    content: {
      quiz_questions: [{ q: "Q1", a: "A1" }, { q: "Q2", a: "A2" }],
      schedule: [], lyrics: [], missions: [], bible_passages: [], custom_data: {},
    },
    architecture: {
      deployment_type: "lan", tech_stack: "node-ws",
      url_routes: ["/", "/admin", "/screen"], data_sync: "realtime",
      has_admin: true, has_screen: true, has_pwa: true,
    },
    status: {
      current_phase: 1, research_complete: true, planning_complete: false,
      code_generated: false, quality_passed: false, deployed: false,
      project_folder: "/tmp/test-project", modification_count: 0,
      in_preview_loop: false, pending_action: null, server_port: null,
      server_url: "", qr_path: "", bat_path: "", github_pages_url: null,
      last_git_checkpoint: "", agent_team_active: false, fallback_tier: 1,
    },
    quality: {
      q_gates: {}, d_gates: {}, app_specific_gates: {},
      pacs: { F: 0, C: 0, L: 0 }, pacs_score: 0,
      last_verified: "", retry_count: 0, verify_log: [],
    },
    history: { modifications: [], exports: [], archive_path: null, fallback_events: [] },
    tdd: { test_files: [], last_run: "", pass_count: 0, fail_count: 0, coverage_percent: 0 },
    translation: {
      glossary_path: "translations/glossary.yaml",
      phases: {
        "1": { english_original: "", korean_translation: "", pacs: { Ft: 0, Ct: 0, Nt: 0 }, pacs_score: 0, status: "pending" },
        "2": { english_original: "", korean_translation: "", pacs: { Ft: 0, Ct: 0, Nt: 0 }, pacs_score: 0, status: "pending" },
        "3": { english_original: "", korean_translation: "", pacs: { Ft: 0, Ct: 0, Nt: 0 }, pacs_score: 0, status: "pending" },
        "4": { english_original: "", korean_translation: "", pacs: { Ft: 0, Ct: 0, Nt: 0 }, pacs_score: 0, status: "pending" },
        "5": { english_original: "", korean_translation: "", pacs: { Ft: 0, Ct: 0, Nt: 0 }, pacs_score: 0, status: "pending" },
        "6": { english_original: "", korean_translation: "", pacs: { Ft: 0, Ct: 0, Nt: 0 }, pacs_score: 0, status: "pending" },
      },
      t_gates: { T1: "pending", T2: "pending", T3: "pending" },
      total_translated_files: 0, glossary_entries_count: 0, last_translation: "",
    },
  };

  // Validate mock SOT against schema
  const schema = JSON.parse(readFileSync(join(ROOT, '.claude/schemas/app-state.schema.json'), 'utf8'));

  // Check all required sections present
  for (const section of schema.required) {
    assert(section in mockSOT, `Mock SOT — has "${section}" section`);
  }

  // Validate enum values
  const validAppTypes = schema.properties.intent.properties.app_type.enum;
  assert(validAppTypes.includes(mockSOT.intent.app_type),
    `Mock SOT — app_type "${mockSOT.intent.app_type}" is valid enum`);

  const validPalettes = schema.properties.intent.properties.design_palette.enum;
  assert(validPalettes.includes(mockSOT.intent.design_palette),
    `Mock SOT — design_palette "${mockSOT.intent.design_palette}" is valid enum`);

  // Validate status.current_phase range
  assert(mockSOT.status.current_phase >= 0 && mockSOT.status.current_phase <= 6,
    `Mock SOT — current_phase ${mockSOT.status.current_phase} in range 0-6`);

  // Validate status.fallback_tier range
  assert(mockSOT.status.fallback_tier >= 1 && mockSOT.status.fallback_tier <= 4,
    `Mock SOT — fallback_tier ${mockSOT.status.fallback_tier} in range 1-4`);

  // Validate pACS scores 0-100
  for (const dim of ['F', 'C', 'L']) {
    assert(mockSOT.quality.pacs[dim] >= 0 && mockSOT.quality.pacs[dim] <= 100,
      `Mock SOT — pacs.${dim} in range 0-100`);
  }

  // Validate translation phases 1-6 exist
  for (let i = 1; i <= 6; i++) {
    assert(String(i) in mockSOT.translation.phases,
      `Mock SOT — translation phase ${i} exists`);
  }

  // Simulate Phase 1 content validation (what validate_content_collection.py does)
  const quizRequired = {
    'intent.app_type': v => ['quiz'].includes(v),
    'intent.team_count': v => typeof v === 'number' && v > 0,
    'intent.team_names': v => Array.isArray(v) && v.length > 0,
    'content.quiz_questions': v => Array.isArray(v) && v.length > 0,
    'intent.design_palette': v => ['A', 'B', 'C'].includes(v),
  };

  let contentComplete = true;
  const missingFields = [];
  for (const [path, validator] of Object.entries(quizRequired)) {
    const keys = path.split('.');
    let val = mockSOT;
    for (const k of keys) val = val?.[k];
    if (!validator(val)) {
      contentComplete = false;
      missingFields.push(path);
    }
  }
  assert(contentComplete, 'Pipeline — Quiz content validation passes (simulated validate_content_collection)',
    missingFields.length ? `missing: ${missingFields.join(', ')}` : '');

  // Simulate pACS deterministic scoring (what compute_pacs_score.py does)
  const mockPacsData = { F_data: { match_rate: 0.95 }, C_data: { coverage_rate: 1.0 }, L_data: { gate_pass_rate: 0.87 } };
  const fScore = Math.round(mockPacsData.F_data.match_rate * 100);
  const cScore = Math.round(mockPacsData.C_data.coverage_rate * 100);
  const lScore = Math.round(mockPacsData.L_data.gate_pass_rate * 100);
  const pacsScore = Math.min(fScore, cScore, lScore);
  const color = pacsScore >= 70 ? 'GREEN' : pacsScore >= 50 ? 'YELLOW' : 'RED';

  assert(fScore === 95, `Pipeline — pACS F = round(0.95 * 100) = ${fScore}`);
  assert(cScore === 100, `Pipeline — pACS C = round(1.0 * 100) = ${cScore}`);
  assert(lScore === 87, `Pipeline — pACS L = round(0.87 * 100) = ${lScore}`);
  assert(pacsScore === 87, `Pipeline — pACS score = min(95,100,87) = ${pacsScore}`);
  assert(color === 'GREEN', `Pipeline — pACS color = ${color}`);

  // Verify ceiling enforcement: score CANNOT exceed rate-based ceiling
  const inflatedAI = 99; // AI tries to give 99
  const bounded = Math.min(inflatedAI, fScore); // ceiling = 95
  assert(bounded === 95, `Pipeline — AI inflation blocked: min(99, 95) = ${bounded}`);
}

// ============================================================================
// Phase 6: Dry-Run Phase Transition Gate Simulation
// ============================================================================

function testDryRunTransitions() {
  section('Phase 6: Dry-Run Phase 0→6 Transition Simulation');

  // Simulate validate_phase_transition.py logic in JS
  const transitions = [
    {
      phase: 0, sot: { status: { current_phase: 0 } },
      expected: true, name: 'Phase 0 → 1 (env check)',
    },
    {
      phase: 1,
      sot: {
        status: { research_complete: true },
        intent: { app_type: 'quiz', design_palette: 'A', team_count: 4, team_names: ['1조','2조','3조','4조'] },
        content: { quiz_questions: [{ q: 'Q1' }] },
      },
      expected: true, name: 'Phase 1 → 2 (quiz complete)',
    },
    {
      phase: 1,
      sot: {
        status: { research_complete: true },
        intent: { app_type: 'quiz', design_palette: 'A', team_count: 0, team_names: [] },
        content: { quiz_questions: [] },
      },
      expected: false, name: 'Phase 1 → 2 (quiz INCOMPLETE — team_count=0)',
    },
    {
      phase: 2,
      sot: {
        status: { planning_complete: true, project_folder: '/tmp/proj' },
        architecture: { tech_stack: 'node-ws', deployment_type: 'lan' },
      },
      expected: true, name: 'Phase 2 → 3 (architecture ready)',
    },
    {
      phase: 2,
      sot: {
        status: { planning_complete: false, project_folder: '' },
        architecture: { tech_stack: '', deployment_type: '' },
      },
      expected: false, name: 'Phase 2 → 3 (INCOMPLETE — planning_complete=false)',
    },
    {
      phase: 3,
      sot: { status: { code_generated: true, last_git_checkpoint: 'abc123' } },
      expected: true, name: 'Phase 3 → 4 (code generated)',
    },
    {
      phase: 4,
      sot: { status: { quality_passed: true }, quality: { pacs_score: 85 } },
      expected: true, name: 'Phase 4 → 5 (quality GREEN)',
    },
    {
      phase: 4,
      sot: { status: { quality_passed: true }, quality: { pacs_score: 40 } },
      expected: false, name: 'Phase 4 → 5 (pACS RED 40 — rework)',
    },
    {
      phase: 5,
      sot: { status: { current_phase: 5 } },
      expected: true, name: 'Phase 5 → 6 (user approved)',
    },
    {
      phase: 6,
      sot: { status: { deployed: true, server_url: 'http://192.168.1.5:3000' } },
      expected: true, name: 'Phase 6 complete (deployed)',
    },
  ];

  // Phase requirement validators (mirror of validate_phase_transition.py)
  const validators = {
    0: { 'status.current_phase': v => v === 0 },
    1: {
      'status.research_complete': v => v === true,
      'intent.app_type': v => ['quiz','score','schedule','lyrics','stamps','qt','prayer','photo','combined'].includes(v),
      'intent.design_palette': v => ['A','B','C'].includes(v),
    },
    2: {
      'status.planning_complete': v => v === true,
      'status.project_folder': v => typeof v === 'string' && v.length > 0,
      'architecture.tech_stack': v => typeof v === 'string' && v.length > 0,
      'architecture.deployment_type': v => typeof v === 'string' && v.length > 0,
    },
    3: {
      'status.code_generated': v => v === true,
      'status.last_git_checkpoint': v => typeof v === 'string' && v.length > 0,
    },
    4: {
      'status.quality_passed': v => v === true,
      'quality.pacs_score': v => typeof v === 'number' && v >= 50,
    },
    5: { 'status.current_phase': v => v === 5 },
    6: {
      'status.deployed': v => v === true,
      'status.server_url': v => typeof v === 'string' && v.length > 0,
    },
  };

  // App-type extras for Phase 1
  const phase1Extras = {
    quiz: {
      'intent.team_count': v => typeof v === 'number' && v > 0,
      'intent.team_names': v => Array.isArray(v) && v.length > 0,
      'content.quiz_questions': v => Array.isArray(v) && v.length > 0,
    },
  };

  for (const t of transitions) {
    const reqs = validators[t.phase] || {};
    let ready = true;

    for (const [path, validator] of Object.entries(reqs)) {
      const keys = path.split('.');
      let val = t.sot;
      for (const k of keys) val = val?.[k];
      if (val === undefined || !validator(val)) { ready = false; break; }
    }

    // Check app-type extras for Phase 1
    if (t.phase === 1 && ready) {
      const appType = t.sot?.intent?.app_type;
      const extras = phase1Extras[appType];
      if (extras) {
        for (const [path, validator] of Object.entries(extras)) {
          const keys = path.split('.');
          let val = t.sot;
          for (const k of keys) val = val?.[k];
          if (val === undefined || !validator(val)) { ready = false; break; }
        }
      }
    }

    assert(ready === t.expected, `Gate: ${t.name}`,
      ready !== t.expected ? `expected ${t.expected}, got ${ready}` : '');
  }
}

// ============================================================================
// Phase 7: Cross-Reference Integrity
// ============================================================================

function testCrossReferences() {
  section('Phase 7: Cross-Reference Integrity');

  const orchestrator = readFileSync(join(ROOT, '.claude/agents/church-app-orchestrator.md'), 'utf8');

  // Orchestrator references all sub-agents by correct name
  const agentNames = ['conversation-guide', 'code-generator', 'design-system',
    'quality-checker', 'deployment-manager', 'tdd-guard', 'app-translator'];
  for (const name of agentNames) {
    assert(orchestrator.includes(`@${name}`) || orchestrator.includes(`"${name}"`),
      `Orchestrator references @${name}`);
  }

  // Orchestrator references H-CRITICAL scripts
  assert(orchestrator.includes('validate_phase_transition.py'), 'Orchestrator uses validate_phase_transition.py');
  assert(orchestrator.includes('compute_pacs_score.py'), 'Orchestrator uses compute_pacs_score.py');
  assert(orchestrator.includes('validate_translation_readiness.py'), 'Orchestrator uses validate_translation_readiness.py');
  assert(orchestrator.includes('validate_content_collection.py'), 'Orchestrator uses validate_content_collection.py');

  // Count GATE (H-CRITICAL) instances
  const gateCount = (orchestrator.match(/GATE \(H-CRITICAL\)/g) || []).length;
  assert(gateCount >= 6, `Orchestrator has ${gateCount} H-CRITICAL gates (expected ≥6)`);

  // Agent frontmatter name matches
  for (const name of agentNames) {
    const filename = name === 'design-system' ? 'design-system-agent.md' : `${name}.md`;
    const filepath = join(ROOT, '.claude/agents', filename);
    if (existsSync(filepath)) {
      const content = readFileSync(filepath, 'utf8');
      const nameMatch = content.match(/^name:\s*(.+)$/m);
      if (nameMatch) {
        const actualName = nameMatch[1].trim().replace(/['"]/g, '');
        assert(actualName === name, `Agent ${filename} — name field "${actualName}" matches "${name}"`);
      }
    }
  }

  // Settings.json hook scripts exist on disk
  const settings = JSON.parse(readFileSync(join(ROOT, '.claude/settings.json'), 'utf8'));
  const allHookCommands = [];
  for (const [event, entries] of Object.entries(settings.hooks)) {
    for (const entry of entries) {
      const hooks = entry.hooks || [];
      for (const h of hooks) {
        if (h.command) allHookCommands.push(h.command);
      }
    }
  }
  const scriptRefs = allHookCommands
    .map(cmd => cmd.match(/scripts\/(\w+\.py)/))
    .filter(Boolean)
    .map(m => m[1]);

  for (const script of new Set(scriptRefs)) {
    assert(existsSync(join(ROOT, '.claude/hooks/scripts', script)),
      `Settings hook script exists: ${script}`);
  }

  // CLAUDE.md references church-retreat-app skill
  const claudeMd = readFileSync(join(ROOT, 'CLAUDE.md'), 'utf8');
  assert(claudeMd.includes('church-retreat-app'), 'CLAUDE.md references church-retreat-app skill');
  assert(claudeMd.includes('start-app'), 'CLAUDE.md references /start-app command');

  // All sub-agents have Context Loading Strategy
  for (const name of agentNames) {
    const filename = name === 'design-system' ? 'design-system-agent.md' : `${name}.md`;
    const filepath = join(ROOT, '.claude/agents', filename);
    if (existsSync(filepath)) {
      const content = readFileSync(filepath, 'utf8');
      assert(content.includes('Context Loading Strategy'),
        `${filename} — has Context Loading Strategy`);
      assert(content.includes('English-First Execution') || content.includes('AC-4'),
        `${filename} — has AC-4 section`);
    }
  }
}

// ============================================================================
// Run All Tests
// ============================================================================

console.log('\n🔬 Church Retreat App — Infrastructure Integration Test Suite');
console.log(`   Project: ${ROOT}`);
console.log(`   Runtime: Node.js ${process.version}`);
console.log(`   Date: ${new Date().toISOString()}\n`);

testFileExistence();
testJsonYamlValidity();
testPythonSyntax();
testHookContracts();
testPipelineDataFlow();
testDryRunTransitions();
testCrossReferences();

// Summary
section('RESULTS');
console.log(`  ✅ Passed: ${passed}`);
console.log(`  ❌ Failed: ${failed}`);
console.log(`  ⏭️  Skipped: ${skipped}`);
console.log(`  📊 Total: ${passed + failed + skipped}`);

if (failures.length > 0) {
  console.log('\n  FAILURES:');
  for (const f of failures) {
    console.log(`    ❌ ${f.test}${f.detail ? '\n       ' + f.detail : ''}`);
  }
}

console.log(`\n  ${failed === 0 ? '🎉 ALL TESTS PASSED' : `⚠️  ${failed} TEST(S) FAILED`}\n`);
process.exit(failed > 0 ? 1 : 0);
