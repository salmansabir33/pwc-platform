import 'package:flutter/material.dart';
import 'tokens.g.dart';

/// Light-only v1.0. Presentation never implies a capability or NGO context.
ThemeData pwcTheme({bool operations = false, bool urdu = false}) {
  final primary = operations ? PwcTokens.opsPrimary : PwcTokens.ngoPrimary;
  final text =
      TextTheme(
        displayLarge: const TextStyle(
          fontSize: 36,
          height: 44 / 36,
          fontWeight: FontWeight.w700,
        ),
        headlineLarge: const TextStyle(
          fontSize: 30,
          height: 38 / 30,
          fontWeight: FontWeight.w600,
        ),
        headlineMedium: const TextStyle(
          fontSize: 24,
          height: 32 / 24,
          fontWeight: FontWeight.w600,
        ),
        headlineSmall: const TextStyle(
          fontSize: 20,
          height: 28 / 20,
          fontWeight: FontWeight.w600,
        ),
        titleLarge: const TextStyle(
          fontSize: 20,
          height: 28 / 20,
          fontWeight: FontWeight.w600,
        ),
        titleMedium: const TextStyle(
          fontSize: 16,
          height: 1.5,
          fontWeight: FontWeight.w600,
        ),
        titleSmall: const TextStyle(
          fontSize: 14,
          height: 20 / 14,
          fontWeight: FontWeight.w600,
        ),
        bodyLarge: const TextStyle(fontSize: 16, height: 1.5),
        bodyMedium: const TextStyle(fontSize: 16, height: 1.5),
        bodySmall: const TextStyle(fontSize: 14, height: 20 / 14),
        labelLarge: const TextStyle(
          fontSize: 16,
          height: 1.5,
          fontWeight: FontWeight.w600,
        ),
        labelMedium: const TextStyle(fontSize: 14, height: 20 / 14),
        labelSmall: const TextStyle(fontSize: 12, height: 1.5),
      ).apply(
        fontFamily: urdu ? PwcTokens.urduFont : PwcTokens.englishFont,
        fontFamilyFallback: const [PwcTokens.urduFont, PwcTokens.englishFont],
        bodyColor: PwcTokens.textPrimary,
        displayColor: PwcTokens.textPrimary,
      );
  final shape = RoundedRectangleBorder(
    borderRadius: BorderRadius.circular(PwcTokens.radii[0]),
  );
  final outline = OutlineInputBorder(
    borderRadius: BorderRadius.circular(PwcTokens.radii[0]),
    borderSide: const BorderSide(color: PwcTokens.controlBorder),
  );
  final scheme = ColorScheme.light(
    primary: primary,
    onPrimary: PwcTokens.surface,
    secondary: primary,
    onSecondary: PwcTokens.surface,
    surface: PwcTokens.surface,
    onSurface: PwcTokens.textPrimary,
    onSurfaceVariant: PwcTokens.textSecondary,
    error: PwcTokens.danger,
    onError: PwcTokens.surface,
    outline: PwcTokens.controlBorder,
    outlineVariant: PwcTokens.border,
    primaryContainer: operations
        ? PwcTokens.infoBackground
        : PwcTokens.successBackground,
    onPrimaryContainer: primary,
    surfaceContainerHighest: PwcTokens.canvas,
  );
  final filled = ButtonStyle(
    minimumSize: const WidgetStatePropertyAll(Size(48, 48)),
    padding: const WidgetStatePropertyAll(
      EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    ),
    shape: WidgetStatePropertyAll(shape),
    foregroundColor: WidgetStateProperty.resolveWith(
      (states) => states.contains(WidgetState.disabled)
          ? PwcTokens.disabledForeground
          : PwcTokens.surface,
    ),
    backgroundColor: WidgetStateProperty.resolveWith((states) {
      if (states.contains(WidgetState.disabled))
        return PwcTokens.disabledBackground;
      if (states.contains(WidgetState.pressed))
        return operations ? PwcTokens.opsPressed : PwcTokens.ngoPressed;
      if (states.contains(WidgetState.hovered))
        return operations ? PwcTokens.opsHover : PwcTokens.ngoHover;
      return primary;
    }),
    side: WidgetStateProperty.resolveWith(
      (states) => states.contains(WidgetState.focused)
          ? const BorderSide(color: PwcTokens.focus, width: 3)
          : BorderSide.none,
    ),
  );
  return ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    colorScheme: scheme,
    scaffoldBackgroundColor: PwcTokens.canvas,
    textTheme: text,
    fontFamily: urdu ? PwcTokens.urduFont : PwcTokens.englishFont,
    visualDensity: VisualDensity.standard,
    materialTapTargetSize: MaterialTapTargetSize.padded,
    focusColor: PwcTokens.focus.withValues(alpha: 0.15),
    disabledColor: PwcTokens.disabledForeground,
    filledButtonTheme: FilledButtonThemeData(style: filled),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: filled.copyWith(elevation: const WidgetStatePropertyAll(0)),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: ButtonStyle(
        minimumSize: const WidgetStatePropertyAll(Size(48, 48)),
        shape: WidgetStatePropertyAll(shape),
        side: WidgetStateProperty.resolveWith(
          (s) => BorderSide(
            color: s.contains(WidgetState.focused) ? PwcTokens.focus : primary,
            width: s.contains(WidgetState.focused) ? 3 : 1,
          ),
        ),
      ),
    ),
    textButtonTheme: TextButtonThemeData(
      style: ButtonStyle(
        minimumSize: const WidgetStatePropertyAll(Size(48, 48)),
        shape: WidgetStatePropertyAll(shape),
      ),
    ),
    iconButtonTheme: const IconButtonThemeData(
      style: ButtonStyle(minimumSize: WidgetStatePropertyAll(Size(48, 48))),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: PwcTokens.surface,
      contentPadding: const EdgeInsets.all(12),
      constraints: const BoxConstraints(minHeight: 48),
      border: outline,
      enabledBorder: outline,
      focusedBorder: outline.copyWith(
        borderSide: const BorderSide(color: PwcTokens.focus, width: 3),
      ),
      errorBorder: outline.copyWith(
        borderSide: const BorderSide(color: PwcTokens.danger),
      ),
      focusedErrorBorder: outline.copyWith(
        borderSide: const BorderSide(color: PwcTokens.danger, width: 3),
      ),
    ),
    cardTheme: CardThemeData(
      color: PwcTokens.surface,
      elevation: 0,
      margin: const EdgeInsets.symmetric(vertical: 8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: PwcTokens.border),
      ),
    ),
    dialogTheme: DialogThemeData(
      backgroundColor: PwcTokens.surface,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
    ),
    appBarTheme: const AppBarTheme(
      backgroundColor: PwcTokens.surface,
      foregroundColor: PwcTokens.textPrimary,
      elevation: 0,
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: PwcTokens.surface,
      indicatorColor: scheme.primaryContainer,
      labelTextStyle: WidgetStatePropertyAll(text.labelSmall),
    ),
    dividerTheme: const DividerThemeData(color: PwcTokens.border, thickness: 1),
    snackBarTheme: const SnackBarThemeData(
      backgroundColor: PwcTokens.textPrimary,
      contentTextStyle: TextStyle(color: PwcTokens.surface, fontSize: 16),
    ),
  );
}
