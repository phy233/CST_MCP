"""Phase 2: Command Buffer integration tests.

Run with:  conda run -n cst39 python <this_file>
From:      cst-runtime-cli/scripts/
"""
import os, sys

project_root = r"D:\My_Program\Python\CST_MCP\skills\cst-runtime-cli\scripts"
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from cst_runtime.core.session import create_blank_project
from cst_runtime.core.project import save_project, change_parameter
from cst_runtime.core.modeling import (
    define_brick, begin_batch, flush_batch, discard_batch,
)

PASS = 0
FAIL = 0

def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {label}")
    else:
        FAIL += 1
        print(f"  [FAIL] {label}  {detail}")


def test_batch_brick_flush(pp):
    """begin -> define_brick * 3 -> flush -> History 只有一条合并条目"""
    print("\n--- Test 1: begin -> define_brick * 3 -> flush ---")
    res = begin_batch(pp, summary="Batch: 3 Bricks")
    check("begin_batch returns success", res.get("status") == "success", res)

    for i in range(3):
        res = define_brick(pp, f"b{i+1}", "component1", "PEC", i*10, i*10+5, 0, 10, 0, 5)
        check(f"define_brick #{i+1} returns success", res.get("status") == "success", res)

    res = flush_batch(pp)
    check("flush_batch returns success", res.get("status") == "success", res)
    print("  >> Manual check: CST History should have ONE entry named 'Batch: 3 Bricks' containing 3 bricks")


def test_batch_brick_param_flush(pp):
    """begin -> create brick -> change parameter -> flush"""
    print("\n--- Test 1.5: begin -> brick -> param -> flush ---")
    res = begin_batch(pp, summary="Batch: Brick + Param")
    check("begin_batch returns success", res.get("status") == "success", res)

    res = define_brick(pp, "b_param", "component1", "PEC", 0, 5, 0, 5, 0, 5)
    check("define_brick returns success", res.get("status") == "success", res)

    res = change_parameter(pp, "test_param", "10")
    check("change_parameter returns success", res.get("status") == "success", res)

    res = flush_batch(pp)
    check("flush_batch returns success", res.get("status") == "success", res)
    print("  >> Manual check: CST History should have ONE entry named 'Batch: Brick + Param' with both operations")


def test_batch_50_bricks(pp):
    """begin -> 50 bricks -> flush"""
    print("\n--- Test 1.6: begin -> 50 bricks -> flush ---")
    res = begin_batch(pp, summary="Batch: 50 Bricks")
    check("begin_batch returns success", res.get("status") == "success", res)

    for i in range(50):
        res = define_brick(pp, f"perf_b{i}", "component1", "PEC", 0, 1, 0, 1, i, i+0.5)
        if res.get("status") != "success":
            check(f"define_brick #{i} failed", False, res)
            break
    else:
        check("50 define_brick calls buffered successfully", True)

    import time
    t0 = time.time()
    res = flush_batch(pp)
    t1 = time.time()
    check("flush_batch returns success", res.get("status") == "success", res)
    print(f"  >> Performance: Flushed 50 bricks in {t1 - t0:.2f} seconds")


def test_empty_flush(pp):
    """begin -> flush -> 空 batch 不调用 COM"""
    print("\n--- Test 2: begin -> flush (empty) ---")
    res = begin_batch(pp, summary="Empty Batch")
    check("begin_batch returns success", res.get("status") == "success", res)

    res = flush_batch(pp)
    check("flush empty batch returns success", res.get("status") == "success", res)
    check("flush empty batch has message", "empty" in res.get("message", "").lower(), res)


def test_double_begin(pp):
    """begin -> begin -> Error"""
    print("\n--- Test 3: begin -> begin (error) ---")
    res = begin_batch(pp, summary="First")
    check("first begin_batch returns success", res.get("status") == "success", res)

    res = begin_batch(pp, summary="Second")
    check("second begin_batch returns error", res.get("status") == "error", res)

    # 清理
    discard_batch(pp)


def test_begin_discard(pp):
    """begin -> discard -> Success"""
    print("\n--- Test 4: begin -> discard ---")
    res = begin_batch(pp, summary="Will Discard")
    check("begin_batch returns success", res.get("status") == "success", res)

    res = discard_batch(pp)
    check("discard_batch returns success", res.get("status") == "success", res)

    # 确认 batch 已清除：flush 应报错
    res = flush_batch(pp)
    check("flush after discard returns error", res.get("status") == "error", res)


def test_discard_drops_commands(pp):
    """begin -> define_brick -> discard -> History 没有变化"""
    print("\n--- Test 5: begin -> define_brick -> discard ---")
    res = begin_batch(pp, summary="Discard With Commands")
    check("begin_batch returns success", res.get("status") == "success", res)

    res = define_brick(pp, "ghost_brick", "component1", "PEC", 0, 5, 0, 5, 0, 5)
    check("define_brick returns success (buffered)", res.get("status") == "success", res)

    res = discard_batch(pp)
    check("discard_batch returns success", res.get("status") == "success", res)
    print("  >> Manual check: CST History should NOT contain 'ghost_brick'")


def main():
    print("=== Phase 2: Command Buffer Tests ===\n")

    print("0. Creating blank project...")
    res = create_blank_project("test_buffer")
    if res.get("status") != "success":
        print(f"FAILED to create project: {res}")
        return
    pp = res["project_path"]
    print(f"   Project: {pp}")

    test_batch_brick_flush(pp)
    test_batch_brick_param_flush(pp)
    test_batch_50_bricks(pp)
    test_empty_flush(pp)
    test_double_begin(pp)
    test_begin_discard(pp)
    test_discard_drops_commands(pp)

    print("\n--- Saving project ---")
    res = save_project(pp)
    check("save_project returns success", res.get("status") == "success", res)

    print(f"\n=== Results: {PASS} passed, {FAIL} failed ===")
    if FAIL > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
