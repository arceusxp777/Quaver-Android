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

# 3) Trazas y captura de errores en WobbleGame.LoadContent y QuaverGame.LoadContent
wg = root / "Wobble" / "Wobble" / "WobbleGame.cs"
if wg.is_file():
    wt = wg.read_text(encoding="utf-8-sig")
    old_wl = "            SpriteBatch = new SpriteBatch(GraphicsDevice);\n            WobbleAssets.Load();"
    new_wl = (
        '            global::Wobble.Logging.AndroidDiagnostics.Trace("WobbleGame.LoadContent start gd=" + (GraphicsDevice != null));\n'
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
        wg.write_text(wt.replace(old_wl, new_wl), encoding="utf-8")

qg = root / "Quaver.Shared" / "QuaverGame.cs"
if qg.is_file():
    qt = qg.read_text(encoding="utf-8-sig")
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
        qg.write_text(qt, encoding="utf-8")

# 4) MainActivity: boton LOGS visible sobre el juego, estado en vivo y ShowReport legible
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

            foreach (var dir in new[] { "Songs", "Skins", "Screenshots", "Replays", "Backup", "Logs" })
            {
                try { Directory.CreateDirectory(Path.Combine(dataDir, dir)); } catch { }
            }

            if (File.Exists(_crashFile))
            {
                ShowReport(File.ReadAllText(_crashFile));
                return;
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
            AndroidDiagnostics.Trace("05.SetContentView view=" + (_gameView != null));

            var rootFrame = new FrameLayout(this);
            rootFrame.SetBackgroundColor(global::Android.Graphics.Color.Black);
            if (_gameView != null)
                rootFrame.AddView(_gameView);

            _statusText = new TextView(this) { Text = "Iniciando Quaver..." };
            _statusText.SetTextColor(global::Android.Graphics.Color.Yellow);
            _statusText.SetBackgroundColor(global::Android.Graphics.Color.Argb(160, 0, 0, 0));
            _statusText.SetPadding(16, 8, 16, 8);
            _statusText.TextSize = 12;
            rootFrame.AddView(_statusText, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WrapContent, ViewGroup.LayoutParams.WrapContent,
                GravityFlags.Top | GravityFlags.Left));

            var logsBtn = new Button(this) { Text = "LOGS" };
            logsBtn.SetBackgroundColor(global::Android.Graphics.Color.Argb(210, 180, 30, 30));
            logsBtn.SetTextColor(global::Android.Graphics.Color.White);
            logsBtn.Click += (s, e) => ShowReport(BuildLogText());
            rootFrame.AddView(logsBtn, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WrapContent, ViewGroup.LayoutParams.WrapContent,
                GravityFlags.Top | GravityFlags.Right));

            SetContentView(rootFrame);

            _handler = new Handler(Looper.MainLooper);
            ScheduleTracePoll();

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
                sb.AppendLine("Dispositivo: " + Build.Manufacturer + " " + Build.Model + " / Android " + Build.VERSION.Release + " (API " + (int)Build.VERSION.SdkInt + ")");
                sb.AppendLine();
                sb.AppendLine(body);
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
