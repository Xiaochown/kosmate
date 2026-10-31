import sys

sys.path.insert(0, "/root/kosmate")
from kos import memory  # noqa: E402

memory.init()
print("stats awal:", memory.stats())

fid = memory.add_fact("user", "tes hapus", "fakta sementara untuk uji delete", 0.5)
print("tambah fakta id:", fid)

hits = memory.search_facts("fakta sementara")
print("cari sebelum hapus:", len(hits), "hit")
assert any(h["id"] == fid for h in hits), "fakta baru gak ketemu di FTS!"

ok = memory.delete_fact(fid)
print("delete ->", ok)

hits2 = memory.search_facts("fakta sementara")
print("cari sesudah hapus:", [h["id"] for h in hits2])

assert ok is True
assert all(h["id"] != fid for h in hits2), "fakta masih muncul setelah dihapus!"

# episode search juga harus jalan
eid = memory.add_episode("user", "uji pencarian episode tentang packet tracer", "test")
res = memory.search_episodes("packet tracer")
print("episode match:", [r["id"] for r in res], "(baru:", eid, ")")
assert any(r["id"] == eid for r in res)

print("ctx:", repr(memory.context_block("packet tracer")[:120]))
print("\nSEMUA TES MEMORI LOLOS")
