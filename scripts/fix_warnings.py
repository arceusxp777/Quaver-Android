import pathlib
import sys

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")

# 1) CS0659 en Quaver.API (TimingGroup y ScrollGroup)
tg = root / "Quaver.API" / "Quaver.API" / "Maps" / "Structures" / "TimingGroup.cs"
if tg.is_file():
    t = tg.read_text(encoding="utf-8-sig")
    if "GetHashCode()" not in t:
        t = t.replace(
            "            return Equals((TimingGroup)obj);\n        }",
            "            return Equals((TimingGroup)obj);\n        }\n\n"
            "        public override int GetHashCode()\n"
            "        {\n"
            "            unchecked\n"
            "            {\n"
            "                return ((ColorRgb != null ? ColorRgb.GetHashCode() : 0) * 397) ^ Hidden.GetHashCode();\n"
            "            }\n"
            "        }",
        )
        tg.write_text(t, encoding="utf-8")
        print("fix_warnings: TimingGroup.cs OK")

sg = root / "Quaver.API" / "Quaver.API" / "Maps" / "Structures" / "ScrollGroup.cs"
if sg.is_file():
    t = sg.read_text(encoding="utf-8-sig")
    if "GetHashCode()" not in t:
        t = t.replace(
            "            return Equals((ScrollGroup)obj);\n        }",
            "            return Equals((ScrollGroup)obj);\n        }\n\n"
            "        public override int GetHashCode()\n"
            "        {\n"
            "            unchecked\n"
            "            {\n"
            "                var hashCode = base.GetHashCode();\n"
            "                hashCode = (hashCode * 397) ^ InitialScrollVelocity.GetHashCode();\n"
            "                if (ScrollVelocities != null)\n"
            "                    foreach (var sv in ScrollVelocities)\n"
            "                        hashCode = (hashCode * 397) ^ SliderVelocityInfo.ByValueComparer.GetHashCode(sv);\n"
            "                if (ScrollSpeedFactors != null)\n"
            "                    foreach (var ssf in ScrollSpeedFactors)\n"
            "                        hashCode = (hashCode * 397) ^ ScrollSpeedFactorInfo.ByValueComparer.GetHashCode(ssf);\n"
            "                return hashCode;\n"
            "            }\n"
            "        }",
        )
        sg.write_text(t, encoding="utf-8")
        print("fix_warnings: ScrollGroup.cs OK")

# 2) Silenciar XML docs de submodulos (CS1570, CS1572, CS1574) en todos los csproj
extra = ";CS1570;CS1572;CS1574"
for rel in (
    "Quaver.API/Quaver.API/Quaver.API.csproj",
    "Wobble/Wobble/Wobble.csproj",
    "Wobble/Wobble.Extended/Wobble.Extended.csproj",
    "Quaver.Shared/Quaver.Shared.csproj",
    "android-head/QuaverAndroid.csproj",
):
    p = root / rel
    if not p.is_file():
        continue
    txt = p.read_text(encoding="utf-8-sig")
    if "CS1570" not in txt and "</NoWarn>" in txt:
        txt = txt.replace("</NoWarn>", f"{extra}</NoWarn>")
        p.write_text(txt, encoding="utf-8")
        print(f"fix_warnings: NoWarn en {rel} OK")
