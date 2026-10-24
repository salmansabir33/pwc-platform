import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

export const english = {
  ngoTitle: "NGO Web Portal",
  opsTitle: "PWC Operations",
  skip: "Skip to main content",
  navigation: "Foundation navigation",
  overview: "Foundation overview",
  accessibility: "Language & accessibility",
  states: "Interface states",
  language: "Display language",
  menu: "Toggle navigation",
  closeMenu: "Close navigation",
  environment: "W1 · Development foundation",
  disconnected: "Live services are not connected",
  eyebrow: "PAKISTAN WELFARE CLUB",
  heading: "A clear foundation for independent impact.",
  opsHeading: "A distinct space for responsible operations.",
  intro:
    "This is the web foundation—not an active NGO workspace. No personal or organizational records are loaded.",
  opsIntro:
    "This console has its own routes, session lifecycle and build. Signing in will not grant operational or NGO authority.",
  foundation: "Foundation",
  available: "Available for review",
  gated: "Separately gated",
  shellTitle: "Built as separate surfaces",
  shellBody:
    "Shared design primitives. Independent applications, routes and private state.",
  authTitle: "Personal security",
  authBody:
    "Sign-in, registration and MFA journeys are not enabled. Live integration belongs to W2.",
  contextTitle: "Real NGO workspaces",
  contextBody:
    "Context discovery and private records require approved authority and backend contracts in W3.",
  boundaryTitle: "A deliberate security boundary",
  boundaryBody:
    "Browser cookie sessions and CSRF are the approved model. Backend authorization—not navigation or a role label—decides access.",
  nextTitle: "What this foundation includes",
  nextBody:
    "Responsive shells, accessible controls, language direction, safe interface states and tested API infrastructure. No live API requests are made.",
  screensTitle: "Screen readiness references",
  screensBody:
    "Canonical identifiers are retained for traceability. These are not links to implemented business workflows.",
  screen: "Screen",
  meaning: "Reference",
  readiness: "Readiness",
  id01: "Register / Sign In",
  id02: "Personal Profile",
  id03: "My Affiliations",
  id04: "Workspaces Switcher",
  id05: "Privacy & Security",
  org04: "Organization Overview",
  ops01: "Audit, Support and Recovery",
  later: "Backend and policy required",
  specimenTitle: "Language & accessibility",
  specimenIntro:
    "An infrastructure specimen using local component state only. It does not submit data or change an account.",
  sampleTitle: "A small, direction-aware form",
  sampleLabel: "Example display label",
  sampleHint: "Use synthetic text only. Nothing is sent or saved.",
  sampleAction: "Test local feedback",
  sampleResult: "Local interaction complete. Nothing was submitted or saved.",
  sampleError: "Enter an example label to test this control.",
  directionTitle: "English / Urdu specimen",
  directionBody:
    "Switch the display language to check text direction, focus and layout. This is not a complete platform translation.",
  mixed: "Mixed-direction identifier",
  focusNote:
    "Try the page with a keyboard. Every control has a visible focus state; text and status do not rely on color alone.",
  statesTitle: "Interface states",
  statesIntro:
    "Static, synthetic component specimens—not a running business process.",
  loadingTitle: "Loading specimen",
  loadingBody: "Preparing an interface. No network request is running.",
  emptyTitle: "Empty specimen",
  emptyBody:
    "No synthetic items to show. This is not a result from an NGO account.",
  errorTitle: "Error specimen",
  errorBody:
    "An example safe error. Raw server messages, secrets and personal information are not displayed.",
  notFound: "This route is not available",
  notFoundBody:
    "Only foundation routes exist here. Authentication and business workflows have not been enabled.",
  back: "Return to foundation",
  footer: "W1 foundation · No live authentication or organizational data",
  target: "Accessibility target: WCAG 2.2 AA",
} as const;
type Key = keyof typeof english;
export const urdu: Record<Key, string> = {
  ngoTitle: "این جی او ویب پورٹل",
  opsTitle: "پی ڈبلیو سی آپریشنز",
  skip: "مرکزی مواد پر جائیں",
  navigation: "بنیادی نیویگیشن",
  overview: "بنیادی جائزہ",
  accessibility: "زبان اور رسائی",
  states: "انٹرفیس کی حالتیں",
  language: "نمائش کی زبان",
  menu: "نیویگیشن کھولیں",
  closeMenu: "نیویگیشن بند کریں",
  environment: "W1 · ترقیاتی بنیاد",
  disconnected: "براہ راست خدمات منسلک نہیں ہیں",
  eyebrow: "پاکستان ویلفیئر کلب",
  heading: "آزاد فلاحی کام کے لیے واضح بنیاد۔",
  opsHeading: "ذمہ دارانہ انتظام کے لیے الگ جگہ۔",
  intro:
    "یہ ویب کی بنیاد ہے، فعال تنظیمی ورک اسپیس نہیں۔ کوئی ذاتی یا تنظیمی ریکارڈ لوڈ نہیں ہوتا۔",
  opsIntro:
    "اس کنسول کے راستے، سیشن اور بلڈ الگ ہیں۔ سائن ان سے تنظیمی اختیارات حاصل نہیں ہوں گے۔",
  foundation: "بنیاد",
  available: "جائزے کے لیے دستیاب",
  gated: "الگ منظوری درکار",
  shellTitle: "الگ انٹرفیس",
  shellBody:
    "ڈیزائن کے بنیادی اجزا مشترک ہیں۔ ایپلی کیشن، راستے اور نجی حالت الگ ہیں۔",
  authTitle: "ذاتی سکیورٹی",
  authBody:
    "سائن ان، رجسٹریشن اور ایم ایف اے فعال نہیں۔ براہ راست انضمام W2 میں ہوگا۔",
  contextTitle: "حقیقی تنظیمی ورک اسپیس",
  contextBody:
    "نجی ریکارڈ اور ورک اسپیس کے لیے W3 میں تصدیق شدہ اختیار اور بیک اینڈ معاہدے درکار ہیں۔",
  boundaryTitle: "واضح حفاظتی حد",
  boundaryBody:
    "براؤزر کوکی اور سی ایس آر ایف منظور شدہ طریقہ ہیں۔ رسائی کا فیصلہ بیک اینڈ کرتا ہے، نیویگیشن یا عہدے کا نام نہیں۔",
  nextTitle: "اس بنیاد میں کیا شامل ہے",
  nextBody:
    "جواب دہ ترتیب، قابل رسائی اجزا، زبان کی سمت اور آزمودہ اے پی آئی ڈھانچہ۔ کوئی براہ راست درخواست نہیں کی جاتی۔",
  screensTitle: "سکرین کی تیاری کے حوالے",
  screensBody:
    "اصل شناختی نمبرز حوالہ کے لیے برقرار ہیں۔ یہ فعال کاروباری صفحات کے لنکس نہیں۔",
  screen: "سکرین",
  meaning: "حوالہ",
  readiness: "تیاری",
  id01: "رجسٹریشن / سائن ان",
  id02: "ذاتی پروفائل",
  id03: "میری وابستگیاں",
  id04: "ورک اسپیس کا انتخاب",
  id05: "رازداری اور سکیورٹی",
  org04: "تنظیم کا جائزہ",
  ops01: "آڈٹ، معاونت اور بحالی",
  later: "بیک اینڈ اور پالیسی درکار",
  specimenTitle: "زبان اور رسائی",
  specimenIntro:
    "یہ مقامی حالت کا نمونہ ہے۔ کوئی ڈیٹا بھیجا نہیں جاتا اور اکاؤنٹ تبدیل نہیں ہوتا۔",
  sampleTitle: "سمت کے مطابق چھوٹا فارم",
  sampleLabel: "مثالی نام",
  sampleHint: "صرف فرضی متن استعمال کریں۔ کچھ بھی بھیجا یا محفوظ نہیں ہوتا۔",
  sampleAction: "مقامی ردعمل آزمائیں",
  sampleResult: "مقامی عمل مکمل ہوا۔ کچھ بھی بھیجا یا محفوظ نہیں ہوا۔",
  sampleError: "اس کنٹرول کو آزمانے کے لیے مثالی نام لکھیں۔",
  directionTitle: "انگریزی / اردو نمونہ",
  directionBody:
    "زبان تبدیل کر کے متن کی سمت، فوکس اور ترتیب آزمائیں۔ یہ مکمل پلیٹ فارم کا ترجمہ نہیں۔",
  mixed: "مخلوط سمت کا شناختی نمبر",
  focusNote:
    "کی بورڈ سے صفحہ آزمائیں۔ ہر کنٹرول کا فوکس واضح ہے اور حالت صرف رنگ سے ظاہر نہیں ہوتی۔",
  statesTitle: "انٹرفیس کی حالتیں",
  statesIntro: "اجزا کے جامد، فرضی نمونے؛ کوئی کاروباری عمل جاری نہیں۔",
  loadingTitle: "لوڈنگ کا نمونہ",
  loadingBody: "انٹرفیس کی تیاری کا نمونہ۔ کوئی نیٹ ورک درخواست جاری نہیں۔",
  emptyTitle: "خالی حالت کا نمونہ",
  emptyBody:
    "کوئی فرضی ریکارڈ موجود نہیں۔ یہ کسی تنظیم کے اکاؤنٹ کا نتیجہ نہیں۔",
  errorTitle: "خرابی کا نمونہ",
  errorBody:
    "محفوظ خرابی کی مثال۔ اصل سرور پیغام، راز یا ذاتی معلومات نہیں دکھائی جاتیں۔",
  notFound: "یہ راستہ دستیاب نہیں",
  notFoundBody:
    "یہاں صرف بنیادی صفحات ہیں۔ تصدیق اور کاروباری کام فعال نہیں کیے گئے۔",
  back: "بنیادی صفحے پر واپس جائیں",
  footer: "W1 بنیاد · براہ راست تصدیق یا تنظیمی ڈیٹا نہیں",
  target: "رسائی کا ہدف: WCAG 2.2 AA",
};
export type Locale = "en" | "ur";
type LocaleContext = {
  locale: Locale;
  direction: "ltr" | "rtl";
  setLocale: (locale: Locale) => void;
  t: (key: Key) => string;
};
const Context = createContext<LocaleContext | null>(null);
export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>("en");
  const direction: "ltr" | "rtl" = locale === "ur" ? "rtl" : "ltr";
  useEffect(() => {
    const previous = {
      lang: document.documentElement.lang,
      dir: document.documentElement.dir,
    };
    document.documentElement.lang = locale;
    document.documentElement.dir = direction;
    return () => {
      document.documentElement.lang = previous.lang;
      document.documentElement.dir = previous.dir;
    };
  }, [locale, direction]);
  const value = useMemo(
    () => ({
      locale,
      direction,
      setLocale,
      t: (key: Key) => (locale === "ur" ? urdu : english)[key],
    }),
    [locale, direction],
  );
  return <Context value={value}>{children}</Context>;
}
export function useLocale(): LocaleContext {
  const value = useContext(Context);
  if (!value) throw new Error("Locale provider required");
  return value;
}
