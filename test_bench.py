import bench
ref = "Welcome to the Monro Inc call. Monro Shock and Brake saw growth. Monro again. NTB stores too."
assert bench.count("Monro", ref) == 3 and bench.count("monro shock", ref) == 1 and bench.count("Mon", ref) == 0
r, n = bench.term_recall(["Monro", "NTB"], ref, "welcome to the monroe call monro shock ntb")
assert n == 4 and abs(r - 2 / 4) < 1e-9, (r, n)
o = bench.oracle_terms(ref, ["Monro", "Monro Shock", "Acme"]); assert o == ["Monro Shock", "Monro"]
doc = ("Monro Shock and Brake operates Car-X locations. Monro Shock and Brake grew. Car-X expanded. The NTB brand and NTB stores. "
       "Our stores sell tires. The company sells tires and services tires. Securities and Exchange Commission. Tires matter.")
t = bench.extract_terms(doc)
assert "Monro Shock" in " | ".join(t) and "NTB" in t and "Car-X" in t and "Tires" not in t, t
print("all tests passed")
