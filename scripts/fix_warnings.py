from pathlib import Path
import sys

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

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
            "                var hashCode = (InitialScrollVelocity != null ? InitialScrollVelocity.GetHashCode() : 0);\n"
            "                hashCode = (hashCode * 397) ^ ColorRgb.GetHashCode();\n"
            "                hashCode = (hashCode * 397) ^ Hidden.GetHashCode();\n"
            "                return hashCode;\n"
            "            }\n"
            "        }",
        )
        tg.write_text(t, encoding="utf-8")

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

# 2) Silenciar XML docs de submodulos (CS1570, CS1572, CS1574)
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

# 3) ConfigManager & StructuredConfigManager: evitar deadlock en hilo UI + ruta valida de SteamWorkshopDirectory en Android
cm = root / "Quaver.Shared" / "Config" / "ConfigManager.cs"
if cm.is_file():
    ct = cm.read_text(encoding="utf-8-sig")
    cm_changed = False
    if "internal static async Task WriteConfigFileAsync()" in ct:
        ct = ct.replace(
            "internal static async Task WriteConfigFileAsync()",
            "internal static Task WriteConfigFileAsync()",
        )
        ct = ct.replace(
            "await sw.WriteLineAsync(sb.ToString());",
            "sw.WriteLine(sb.ToString());",
        )
        ct = ct.replace(
            "            LastWrite = GameBase.Game?.TimeRunning ?? -1;\n        }",
            "            LastWrite = GameBase.Game?.TimeRunning ?? -1;\n            return Task.CompletedTask;\n        }",
        )
        cm_changed = True
    old_ws = '_steamWorkshopDirectory = $"{GameDirectory.Value}/../../workshop/content/{SteamManager.ApplicationId}";'
    new_ws = (
        '_steamWorkshopDirectory = global::System.OperatingSystem.IsAndroid()\n'
        '                ? $"{GameDirectory.Value}/Workshop"\n'
        '                : $"{GameDirectory.Value}/../../workshop/content/{SteamManager.ApplicationId}";'
    )
    if old_ws in ct and 'GameDirectory.Value}/Workshop' not in ct:
        ct = ct.replace(old_ws, new_ws)
        cm_changed = True
    if cm_changed:
        cm.write_text(ct, encoding="utf-8")

scm = root / "Quaver.Shared" / "Config" / "StructuredConfigManager.cs"
if scm.is_file():
    st = scm.read_text(encoding="utf-8-sig")
    if "internal static async Task WriteConfigFileAsync()" in st:
        st = st.replace(
            "internal static async Task WriteConfigFileAsync()",
            "internal static Task WriteConfigFileAsync()",
        )
        st = st.replace(
            "await using var sw = new StreamWriter(configFilePath);",
            "using var sw = new StreamWriter(configFilePath);",
        )
        st = st.replace(
            "        LastWrite = GameBase.Game?.TimeRunning ?? -1;\n    }",
            "        LastWrite = GameBase.Game?.TimeRunning ?? -1;\n        return Task.CompletedTask;\n    }",
        )
        scm.write_text(st, encoding="utf-8")

# 4) WobbleGame: MainThreadId en hilo GL, evitar ImGui/cimgui en Android Debug, y trazas Initialize/LoadContent
wg = root / "Wobble" / "Wobble" / "WobbleGame.cs"
if wg.is_file():
    wt = wg.read_text(encoding="utf-8-sig")
    changed = False
    if "public int MainThreadId { get; }" in wt:
        wt = wt.replace(
            "public int MainThreadId { get; }",
            "public int MainThreadId { get; private set; }",
        )
        changed = True
    old_init = (
        "        protected override void Initialize()\n"
        "        {\n"
        '            global::Wobble.Logging.AndroidDiagnostics.Trace("WobbleGame.Initialize profile=" + GraphicsDevice?.GraphicsProfile);\n'
        '            Resources.AddStore(new DllResourceStore("Wobble.Resources.dll"));\n\n'
        "            LogManager.Initialize();\n"
        "            AudioManager.Initialize(DevicePeriod, DeviceBufferLength);\n"
        "            Window.ClientSizeChanged += WindowManager.OnClientSizeChanged;\n\n"
        "            base.Initialize();\n"
        "        }"
    )
    new_init = (
        "        protected override void Initialize()\n"
        "        {\n"
        "            MainThreadId = System.Threading.Thread.CurrentThread.ManagedThreadId;\n"
        '            global::Wobble.Logging.AndroidDiagnostics.Trace("WobbleGame.Initialize start tid=" + MainThreadId + " profile=" + GraphicsDevice?.GraphicsProfile);\n'
        "            try\n"
        "            {\n"
        '                Resources.AddStore(new DllResourceStore("Wobble.Resources.dll"));\n\n'
        "                LogManager.Initialize();\n"
        "                AudioManager.Initialize(DevicePeriod, DeviceBufferLength);\n"
        "                Window.ClientSizeChanged += WindowManager.OnClientSizeChanged;\n\n"
        "                base.Initialize();\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Trace("WobbleGame.Initialize ok");\n'
        "            }\n"
        "            catch (Exception ex)\n"
        "            {\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Fatal("WobbleGame.Initialize", ex);\n'
        "                throw;\n"
        "            }\n"
        "        }"
    )
    if old_init in wt:
        wt = wt.replace(old_init, new_init)
        changed = True
    old_wl = "            SpriteBatch = new SpriteBatch(GraphicsDevice);\n            WobbleAssets.Load();"
    new_wl = (
        "            MainThreadId = System.Threading.Thread.CurrentThread.ManagedThreadId;\n"
        '            global::Wobble.Logging.AndroidDiagnostics.Trace("WobbleGame.LoadContent start tid=" + MainThreadId + " gd=" + (GraphicsDevice != null));\n'
        "            try\n"
        "            {\n"
        "                SpriteBatch = new SpriteBatch(GraphicsDevice);\n"
        "                WobbleAssets.Load();\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Trace("WobbleGame.LoadContent ok");\n'
        "            }\n"
        "            catch (Exception ex)\n"
        "            {\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Fatal("WobbleGame.LoadContent", ex);\n'
        "                throw;\n"
        "            }"
    )
    if old_wl in wt and "WobbleGame.LoadContent start" not in wt:
        wt = wt.replace(old_wl, new_wl)
        changed = True
    elif 'global::Wobble.Logging.AndroidDiagnostics.Trace("WobbleGame.LoadContent start gd=" + (GraphicsDevice != null));' in wt:
        wt = wt.replace(
            'global::Wobble.Logging.AndroidDiagnostics.Trace("WobbleGame.LoadContent start gd=" + (GraphicsDevice != null));',
            'MainThreadId = System.Threading.Thread.CurrentThread.ManagedThreadId;\n            global::Wobble.Logging.AndroidDiagnostics.Trace("WobbleGame.LoadContent start tid=" + MainThreadId + " gd=" + (GraphicsDevice != null));',
        )
        changed = True
    if "#if DEBUG\n            DebugOverlay = new DebugOverlay();\n#endif" in wt:
        wt = wt.replace(
            "#if DEBUG\n            DebugOverlay = new DebugOverlay();\n#endif",
            "#if DEBUG\n            if (!global::System.OperatingSystem.IsAndroid())\n                DebugOverlay = new DebugOverlay();\n#endif",
        )
        changed = True
    if changed:
        wg.write_text(wt, encoding="utf-8")

# 4b) Drawable.~Drawable: proteger Destroy() en el hilo Finalizer para evitar crashes AppDomain si falla un ctor parcial
drw = root / "Wobble" / "Wobble" / "Graphics" / "Drawable.cs"
if drw.is_file():
    dt = drw.read_text(encoding="utf-8-sig")
    old_fin = (
        "        ~Drawable()\n"
        "        {\n"
        "            if (IsDisposed)\n"
        "                return;\n\n"
        "            Destroy();\n"
        "            IsDisposed = true;\n"
        "        }"
    )
    new_fin = (
        "        ~Drawable()\n"
        "        {\n"
        "            if (IsDisposed)\n"
        "                return;\n\n"
        "            try\n"
        "            {\n"
        "                Destroy();\n"
        "            }\n"
        "            catch (Exception ex)\n"
        "            {\n"
        '                try { global::Wobble.Logging.AndroidDiagnostics.Trace("Drawable.Finalize: " + ex.GetType().Name + ": " + ex.Message); } catch { }\n'
        "            }\n\n"
        "            IsDisposed = true;\n"
        "        }"
    )
    if old_fin in dt and "Drawable.Finalize:" not in dt:
        dt = dt.replace(old_fin, new_fin)
        drw.write_text(dt, encoding="utf-8")

# 5) QuaverGame: trazas y captura de errores en Initialize, LoadContent y FirstUpdate
qg = root / "Quaver.Shared" / "QuaverGame.cs"
if qg.is_file():
    qt = qg.read_text(encoding="utf-8-sig")
    q_changed = False
    old_qi = "        protected override void Initialize()\n        {\n            QuaverScreenManager.Initialize();"
    new_qi = (
        "        protected override void Initialize()\n"
        "        {\n"
        '            global::Wobble.Logging.AndroidDiagnostics.Trace("QuaverGame.Initialize start");\n'
        "            try\n"
        "            {\n"
        "                QuaverScreenManager.Initialize();"
    )
    old_qi_end = "            base.Initialize();\n        }\n\n        /// <inheritdoc />\n        /// <summary>\n        ///     LoadContent"
    new_qi_end = (
        "                base.Initialize();\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Trace("QuaverGame.Initialize ok");\n'
        "            }\n"
        "            catch (Exception ex)\n"
        "            {\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Fatal("QuaverGame.Initialize", ex);\n'
        "                throw;\n"
        "            }\n"
        "        }\n\n        /// <inheritdoc />\n        /// <summary>\n        ///     LoadContent"
    )
    if old_qi in qt and old_qi_end in qt and "QuaverGame.Initialize start" not in qt:
        qt = qt.replace(old_qi, new_qi).replace(old_qi_end, new_qi_end)
        q_changed = True

    old_ql = "            base.LoadContent();\n            GlobalIcons.Load();"
    new_ql = (
        '            global::Wobble.Logging.AndroidDiagnostics.Trace("QuaverGame.LoadContent begin");\n'
        "            try\n"
        "            {\n"
        "                base.LoadContent();\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Trace("QuaverGame.LoadContent icons/flags");\n'
        "                GlobalIcons.Load();"
    )
    old_ql_end = "            QuaverScreenManager.ScheduleScreenChange(() => QuaverScreenFactory.CreateInitialization(), true);\n#endif"
    new_ql_end = (
        "                QuaverScreenManager.ScheduleScreenChange(() => QuaverScreenFactory.CreateInitialization(), true);\n"
        "#endif\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Trace("QuaverGame.LoadContent done");\n'
        "            }\n"
        "            catch (Exception ex)\n"
        "            {\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Fatal("QuaverGame.LoadContent", ex);\n'
        "                throw;\n"
        "            }"
    )
    if old_ql in qt and old_ql_end in qt and "QuaverGame.LoadContent begin" not in qt:
        qt = qt.replace(old_ql, new_ql).replace(old_ql_end, new_ql_end)
        q_changed = True

    old_fu = (
        "            if (!FirstUpdateCalled)\n"
        "            {\n"
        "                InitializeFpsLimiting();\n\n"
        "                // Create the online hub on the first update, since it uses text, and we have to wait for things to\n"
        "                // be initialized\n"
        "                OnlineHub = new OnlineHub();\n"
        "                OnlineChat = new OnlineChat();\n"
        "                TooltipManager.TargetEligibilityFilter = target => OnlineChat.AllowsTooltip(target);\n"
        "                VolumeController = new VolumeControl();\n"
        "                FirstUpdateCalled = true;\n"
        "            }"
    )
    new_fu = (
        "            if (!FirstUpdateCalled)\n"
        "            {\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Trace("QuaverGame.FirstUpdate start");\n'
        "                try\n"
        "                {\n"
        "                    InitializeFpsLimiting();\n"
        "                    OnlineHub = new OnlineHub();\n"
        "                    OnlineChat = new OnlineChat();\n"
        "                    TooltipManager.TargetEligibilityFilter = target => OnlineChat.AllowsTooltip(target);\n"
        "                    VolumeController = new VolumeControl();\n"
        "                    FirstUpdateCalled = true;\n"
        '                    global::Wobble.Logging.AndroidDiagnostics.Trace("QuaverGame.FirstUpdate ok");\n'
        "                }\n"
        "                catch (Exception ex)\n"
        "                {\n"
        '                    global::Wobble.Logging.AndroidDiagnostics.Fatal("QuaverGame.FirstUpdate", ex);\n'
        "                    throw;\n"
        "                }\n"
        "            }"
    )
    if old_fu in qt and "QuaverGame.FirstUpdate start" not in qt:
        qt = qt.replace(old_fu, new_fu)
        q_changed = True

    if q_changed:
        qg.write_text(qt, encoding="utf-8")

# 5b) SkinStore, OptionsMenu, OptionsDialog, OptionsItems y EditScreen: evitar DirectoryNotFoundException / NullReferenceException
sk = root / "Quaver.Shared" / "Skinning" / "SkinStore.cs"
if sk.is_file():
    skt = sk.read_text(encoding="utf-8-sig")
    old_gs = (
        "            var skinDirectories = Directory.GetDirectories(ConfigManager.SkinDirectory.Value);\n\n"
        "            var dirs = skinDirectories.Select(dir => new DirectoryInfo(dir).Name);\n"
        "            skins.AddRange(dirs.ToList());\n\n"
        "            var workshopDirectories = Directory.GetDirectories(ConfigManager.SteamWorkshopDirectory.Value);"
    )
    new_gs = (
        "            var skinDir = ConfigManager.SkinDirectory?.Value;\n"
        "            var skinDirectories = !string.IsNullOrEmpty(skinDir) && Directory.Exists(skinDir)\n"
        "                ? Directory.GetDirectories(skinDir)\n"
        "                : global::System.Array.Empty<string>();\n\n"
        "            var dirs = skinDirectories.Select(dir => new DirectoryInfo(dir).Name);\n"
        "            skins.AddRange(dirs.ToList());\n\n"
        "            var workshopDir = ConfigManager.SteamWorkshopDirectory?.Value;\n"
        "            var workshopDirectories = !string.IsNullOrEmpty(workshopDir) && Directory.Exists(workshopDir)\n"
        "                ? Directory.GetDirectories(workshopDir)\n"
        "                : global::System.Array.Empty<string>();"
    )
    if old_gs in skt:
        skt = skt.replace(old_gs, new_gs)
        sk.write_text(skt, encoding="utf-8")

om = root / "Quaver.Shared" / "Screens" / "Options" / "OptionsMenu.cs"
if om.is_file():
    omt = om.read_text(encoding="utf-8-sig")
    old_omd = (
        "        public override void Destroy()\n"
        "        {\n"
        "            // ReSharper disable once DelegateSubtraction\n"
        "            SelectedSection.ValueChanged -= OnSectionChanged;\n"
        "            SelectedSection?.Dispose();\n"
        "            CurrentSearchQuery?.Dispose();\n"
        "            IsOptionFocused?.Dispose();\n\n"
        "            // Make sure to destroy everything that's not visible\n"
        "            foreach (var section in Sections)\n"
        "            {\n"
        "                foreach (var subcategory in section.Subcategories)\n"
        "                {\n"
        "                    foreach (var item in subcategory.Items)\n"
        "                    {\n"
        "                        item?.Destroy();\n"
        "                    }\n"
        "                }\n"
        "            }\n\n"
        "            base.Destroy();\n"
        "        }"
    )
    new_omd = (
        "        public override void Destroy()\n"
        "        {\n"
        "            if (SelectedSection != null)\n"
        "            {\n"
        "                // ReSharper disable once DelegateSubtraction\n"
        "                SelectedSection.ValueChanged -= OnSectionChanged;\n"
        "                SelectedSection.Dispose();\n"
        "            }\n"
        "            CurrentSearchQuery?.Dispose();\n"
        "            IsOptionFocused?.Dispose();\n\n"
        "            // Make sure to destroy everything that's not visible\n"
        "            if (Sections != null)\n"
        "            {\n"
        "                foreach (var section in Sections)\n"
        "                {\n"
        "                    if (section?.Subcategories == null)\n"
        "                        continue;\n\n"
        "                    foreach (var subcategory in section.Subcategories)\n"
        "                    {\n"
        "                        if (subcategory?.Items == null)\n"
        "                            continue;\n\n"
        "                        foreach (var item in subcategory.Items)\n"
        "                        {\n"
        "                            item?.Destroy();\n"
        "                        }\n"
        "                    }\n"
        "                }\n"
        "            }\n\n"
        "            base.Destroy();\n"
        "        }"
    )
    if old_omd in omt:
        omt = omt.replace(old_omd, new_omd)
        om.write_text(omt, encoding="utf-8")

od = root / "Quaver.Shared" / "Screens" / "Options" / "OptionsDialog.cs"
if od.is_file():
    odt = od.read_text(encoding="utf-8-sig")
    if "GlobalInputToken.Dispose();" in odt:
        odt = odt.replace("GlobalInputToken.Dispose();", "GlobalInputToken?.Dispose();")
        od.write_text(odt, encoding="utf-8")

ocs = root / "Quaver.Shared" / "Screens" / "Options" / "Items" / "Custom" / "OptionsItemCustomSkin.cs"
if ocs.is_file():
    ocst = ocs.read_text(encoding="utf-8-sig")
    old_gsi = "            if (skin == null)\n                return 0;"
    new_gsi = "            if (skin == null || string.IsNullOrEmpty(skin.Value))\n                return 0;"
    if old_gsi in ocst:
        ocst = ocst.replace(old_gsi, new_gsi)
        ocs.write_text(ocst, encoding="utf-8")

osr = root / "Quaver.Shared" / "Screens" / "Options" / "Items" / "Custom" / "OptionsItemScreenResolution.cs"
if osr.is_file():
    osrt = osr.read_text(encoding="utf-8-sig")
    old_modes = (
        "            foreach (DisplayMode mode in GraphicsAdapter.DefaultAdapter.SupportedDisplayModes)\n"
        "            {\n"
        '                var option = $"{mode.Width}x{mode.Height}";\n\n'
        "                if (!options.Contains(option))\n"
        "                    options.Add(option);\n"
        "            }"
    )
    new_modes = (
        "            try\n"
        "            {\n"
        "                foreach (DisplayMode mode in GraphicsAdapter.DefaultAdapter.SupportedDisplayModes)\n"
        "                {\n"
        '                    var option = $"{mode.Width}x{mode.Height}";\n\n'
        "                    if (!options.Contains(option))\n"
        "                        options.Add(option);\n"
        "                }\n"
        "            }\n"
        "            catch\n"
        "            {\n"
        "            }"
    )
    if old_modes in osrt and "try\n            {\n                foreach (DisplayMode mode" not in osrt:
        osrt = osrt.replace(old_modes, new_modes)
        osr.write_text(osrt, encoding="utf-8")

oao = root / "Quaver.Shared" / "Screens" / "Options" / "Items" / "Custom" / "OptionsItemAudioOutputDevice.cs"
if oao.is_file():
    oaot = oao.read_text(encoding="utf-8-sig")
    old_ao = (
        "        private static List<string> GetOptions()\n"
        "        {\n"
        "            var options = new List<string>();\n\n"
        "            for (var i = 1; i < Bass.DeviceCount; i++)\n"
        "                options.Add(Bass.GetDeviceInfo(i).Name);\n\n"
        "            return options;\n"
        "        }"
    )
    new_ao = (
        "        private static List<string> GetOptions()\n"
        "        {\n"
        "            var options = new List<string>();\n\n"
        "            try\n"
        "            {\n"
        "                for (var i = 1; i < Bass.DeviceCount; i++)\n"
        "                {\n"
        "                    var name = Bass.GetDeviceInfo(i).Name;\n"
        "                    if (!string.IsNullOrWhiteSpace(name))\n"
        "                        options.Add(name);\n"
        "                }\n"
        "            }\n"
        "            catch\n"
        "            {\n"
        "            }\n\n"
        "            if (options.Count == 0)\n"
        '                options.Add("Default");\n\n'
        "            return options;\n"
        "        }"
    )
    if old_ao in oaot:
        oaot = oaot.replace(old_ao, new_ao)
        oao.write_text(oaot, encoding="utf-8")

es = root / "Quaver.Shared" / "Screens" / "Edit" / "EditScreen.cs"
if es.is_file():
    est = es.read_text(encoding="utf-8-sig")
    old_lp = (
        "        private void LoadPluginsFromDirectory(string dir, bool isWorkshop)\n"
        "        {\n"
        "            foreach (var directory in Directory.GetDirectories(dir))"
    )
    new_lp = (
        "        private void LoadPluginsFromDirectory(string dir, bool isWorkshop)\n"
        "        {\n"
        "            if (string.IsNullOrEmpty(dir) || !Directory.Exists(dir))\n"
        "                return;\n\n"
        "            foreach (var directory in Directory.GetDirectories(dir))"
    )
    if old_lp in est:
        est = est.replace(old_lp, new_lp)
        es.write_text(est, encoding="utf-8")

# 6) MainActivity: HUD visible desde el primer instante + juego en capa inferior
ma = root / "android-head" / "MainActivity.cs"
if ma.is_file():
    ma.write_text(r"""using System;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using Android.App;
using Android.Content;
using Android.Content.PM;
using Android.OS;
using Android.Views;
using Android.Widget;
using Microsoft.Xna.Framework;
using Wobble.Logging;

namespace QuaverAndroid
{
    [Activity(Label = "Quaver", Icon = "@drawable/icon", MainLauncher = true, LaunchMode = LaunchMode.SingleInstance,
        ScreenOrientation = ScreenOrientation.SensorLandscape,
        ConfigurationChanges = ConfigChanges.Orientation | ConfigChanges.Keyboard | ConfigChanges.KeyboardHidden | ConfigChanges.ScreenSize)]
    public class MainActivity : AndroidGameActivity
    {
        private string _crashFile;
        private Quaver.Shared.QuaverGame _game;
        private View _gameView;
        private FrameLayout _rootFrame;
        private TextView _statusText;
        private Handler _handler;

        protected override void OnCreate(Bundle bundle)
        {
            base.OnCreate(bundle);
            Window?.AddFlags(WindowManagerFlags.KeepScreenOn | WindowManagerFlags.Fullscreen);
            var dataDir = FilesDir.AbsolutePath;
            Wobble.WobbleGame.WorkingDirectory = dataDir + "/";
            _crashFile = Path.Combine(dataDir, "informe-fallo.txt");
            HookCrashHandlers();

            foreach (var dir in new[] { "Songs", "Skins", "Screenshots", "Replays", "Backup", "Logs", "Workshop" })
            {
                try { Directory.CreateDirectory(Path.Combine(dataDir, dir)); } catch { }
            }

            if (File.Exists(_crashFile))
            {
                ShowReport(File.ReadAllText(_crashFile));
                return;
            }

            _rootFrame = new FrameLayout(this);
            _rootFrame.SetBackgroundColor(global::Android.Graphics.Color.Black);

            _statusText = new TextView(this) { Text = "Iniciando Quaver..." };
            _statusText.SetTextColor(global::Android.Graphics.Color.Yellow);
            _statusText.SetBackgroundColor(global::Android.Graphics.Color.Argb(160, 0, 0, 0));
            _statusText.SetPadding(16, 8, 16, 8);
            _statusText.TextSize = 12;
            _rootFrame.AddView(_statusText, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WrapContent, ViewGroup.LayoutParams.WrapContent,
                GravityFlags.Top | GravityFlags.Left));

            var logsBtn = new Button(this) { Text = "LOGS" };
            logsBtn.SetBackgroundColor(global::Android.Graphics.Color.Argb(210, 180, 30, 30));
            logsBtn.SetTextColor(global::Android.Graphics.Color.White);
            logsBtn.Click += (s, e) => ShowReport(BuildLogText());
            _rootFrame.AddView(logsBtn, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WrapContent, ViewGroup.LayoutParams.WrapContent,
                GravityFlags.Top | GravityFlags.Right));

            SetContentView(_rootFrame);

            _handler = new Handler(Looper.MainLooper);
            ScheduleTracePoll();

            AndroidDiagnostics.Trace("01.OnCreate dataDir=" + dataDir);

            foreach (var lib in new[] { "bass", "bass_fx", "e_sqlite3", "SkiaSharp", "freetype", "openal32" })
            {
                try
                {
                    global::Java.Lang.JavaSystem.LoadLibrary(lib);
                    AndroidDiagnostics.Trace("LoadLibrary OK: " + lib);
                }
                catch (Exception ex)
                {
                    AndroidDiagnostics.Trace("LoadLibrary WARN " + lib + ": " + ex.Message);
                }
            }

            foreach (var asm in new[] { "Quaver.Resources", "Wobble.Resources" })
            {
                try
                {
                    System.Reflection.Assembly.Load(asm);
                    AndroidDiagnostics.Trace("Assembly.Load OK: " + asm);
                }
                catch (Exception ex)
                {
                    AndroidDiagnostics.Trace("Assembly.Load WARN " + asm + ": " + ex.Message);
                }
            }

            try
            {
                StartQuaver(dataDir + "/");
            }
            catch (Exception e)
            {
                WriteReport(e, "arranque");
                ShowReport(File.Exists(_crashFile) ? File.ReadAllText(_crashFile) : e.ToString());
            }
        }

        private void StartQuaver(string workDir)
        {
            Wobble.WobbleGame.WorkingDirectory = workDir;
            Directory.SetCurrentDirectory(workDir);
            AndroidDiagnostics.Trace("02.Batteries_V2.Init");
            SQLitePCL.Batteries_V2.Init();
            AndroidDiagnostics.Trace("03.ConfigManager.Initialize");
            Wobble.Logging.Logger.Initialize();
            Quaver.Shared.Config.ConfigManager.Initialize();
            Quaver.Shared.Config.StructuredConfigManager.Initialize();
            System.Globalization.CultureInfo.DefaultThreadCurrentCulture = System.Globalization.CultureInfo.InvariantCulture;
            System.Threading.Thread.CurrentThread.CurrentCulture = System.Globalization.CultureInfo.InvariantCulture;
            System.Threading.Thread.CurrentThread.CurrentUICulture = System.Globalization.CultureInfo.InvariantCulture;
            AndroidDiagnostics.Trace("04.new QuaverGame");
            _game = new Quaver.Shared.QuaverGame();
            _gameView = (View)_game.Services.GetService(typeof(View));
            AndroidDiagnostics.Trace("05.AttachGameView view=" + (_gameView != null));

            if (_gameView != null && _rootFrame != null)
            {
                _rootFrame.AddView(_gameView, 0, new FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MatchParent, ViewGroup.LayoutParams.MatchParent));
            }

            AndroidDiagnostics.Trace("06.game.Run()");
            _game.Run();
        }

        private void ScheduleTracePoll()
        {
            _handler?.PostDelayed(() =>
            {
                try
                {
                    var tracePath = Path.Combine(FilesDir.AbsolutePath, "Logs", "boot-trace.log");
                    if (File.Exists(tracePath) && _statusText != null)
                    {
                        var lines = ReadShared(tracePath).TrimEnd().Split('\n');
                        if (lines.Length > 0)
                            _statusText.Text = lines[lines.Length - 1].Trim();
                    }
                }
                catch { }
                ScheduleTracePoll();
            }, 600);
        }

        public override bool DispatchKeyEvent(KeyEvent e)
        {
            if (e != null && e.KeyCode == Keycode.VolumeDown && e.Action == KeyEventActions.Down)
            {
                try { ShowReport(BuildLogText()); }
                catch (Exception ex) { Android.Util.Log.Error("QuaverAndroid", ex.ToString()); }
                return true;
            }
            return base.DispatchKeyEvent(e);
        }

        private void HookCrashHandlers()
        {
            AppDomain.CurrentDomain.UnhandledException += (s, e) => WriteReport(e.ExceptionObject as Exception, "AppDomain");
            Android.Runtime.AndroidEnvironment.UnhandledExceptionRaiser += (s, e) => WriteReport(e.Exception, "Android");
            TaskScheduler.UnobservedTaskException += (s, e) =>
            {
                WriteReport(e.Exception, "UnobservedTask");
                e.SetObserved();
            };
            AndroidDiagnostics.OnFatal += msg =>
            {
                WriteTextReport("TaskHandler/Fatal", msg);
                try
                {
                    RunOnUiThread(() => ShowReport(BuildLogText() + "\n\n=== EXCEPCION ===\n" + msg));
                }
                catch { }
            };
        }

        private void WriteTextReport(string origin, string body)
        {
            try
            {
                var sb = new StringBuilder();
                sb.AppendLine("Quaver Android (comunitario) - informe de fallo");
                sb.AppendLine("Origen: " + origin);
                sb.AppendLine("Hora UTC: " + DateTime.UtcNow.ToString("u"));
                sb.AppendLine("Dispositivo: " + Build.Manufacturer + " " + Build.Model + " / Android " + Build.VERSION.Release + " (API " + (int)Build.SdkInt + ")");
                sb.AppendLine();
                sb.AppendLine(body);
                if (File.Exists(_crashFile) && new FileInfo(_crashFile).Length < 65536)
                    File.AppendAllText(_crashFile, "\n\n--- REGISTRO ADICIONAL ---\n\n" + sb);
                else
                    File.WriteAllText(_crashFile, sb.ToString());
                Android.Util.Log.Error("QuaverAndroid", sb.ToString());
            }
            catch { }
        }

        private void WriteReport(Exception ex, string origin) =>
            WriteTextReport(origin, ex != null ? ex.ToString() : "(sin excepcion)");

        private static string ReadShared(string path)
        {
            using (var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
            using (var sr = new StreamReader(fs))
                return sr.ReadToEnd();
        }

        private string BuildLogText()
        {
            var sb = new StringBuilder();
            sb.AppendLine("Registro de Quaver Android (boot-trace + Logs)");
            var dir = Path.Combine(FilesDir.AbsolutePath, "Logs");
            if (!Directory.Exists(dir))
            {
                sb.AppendLine("(no existe la carpeta de registros: " + dir + ")");
                return sb.ToString();
            }
            foreach (var file in Directory.GetFiles(dir, "*.log"))
            {
                string[] lines;
                try
                {
                    lines = ReadShared(file).Split(new[] { Convert.ToChar(10) });
                }
                catch (Exception e)
                {
                    sb.AppendLine("No se pudo leer " + file + ": " + e.Message);
                    continue;
                }
                sb.AppendLine();
                sb.AppendLine("=== " + Path.GetFileName(file) + " (" + lines.Length + " lineas) ===");
                for (var i = Math.Max(0, lines.Length - 120); i < lines.Length; i++)
                    sb.AppendLine(lines[i].TrimEnd(Convert.ToChar(13)));
            }
            return sb.ToString();
        }

        private void ShowReport(string text)
        {
            if (_gameView != null)
                _gameView.Visibility = ViewStates.Gone;

            var layout = new LinearLayout(this) { Orientation = Orientation.Vertical };
            layout.SetBackgroundColor(global::Android.Graphics.Color.Rgb(20, 20, 28));
            layout.SetPadding(32, 32, 32, 32);

            var title = new TextView(this) { Text = "Quaver Android: informe" };
            title.TextSize = 18;
            title.SetTextColor(global::Android.Graphics.Color.White);

            var copy = new Button(this) { Text = "Copiar informe" };
            copy.Click += (s, e) =>
            {
                var cm = (ClipboardManager)GetSystemService(ClipboardService);
                cm.PrimaryClip = ClipData.NewPlainText("informe", text);
                Toast.MakeText(this, "Informe copiado", ToastLength.Short).Show();
            };

            var close = new Button(this) { Text = "Borrar informe y cerrar" };
            close.Click += (s, e) =>
            {
                try { File.Delete(_crashFile); } catch { }
                Android.OS.Process.KillProcess(Android.OS.Process.MyPid());
            };

            var body = new TextView(this) { Text = text };
            body.TextSize = 11;
            body.SetTextColor(global::Android.Graphics.Color.White);
            body.SetTextIsSelectable(true);

            layout.AddView(title);
            layout.AddView(copy);
            layout.AddView(close);
            layout.AddView(body);

            var scroll = new ScrollView(this);
            scroll.SetBackgroundColor(global::Android.Graphics.Color.Rgb(20, 20, 28));
            scroll.AddView(layout);
            SetContentView(scroll);
        }
    }
}
""", encoding="utf-8")
