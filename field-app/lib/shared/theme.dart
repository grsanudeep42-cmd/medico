// Dark teal medical theme for the Medico field-app.
import 'package:flutter/material.dart';


const _fontFamily = 'Roboto'; // ships with Material

// ── Colour palette ──────────────────────────────────────────────────────────
const kColorBackground = Color(0xFF0A1628);
const kColorSurface = Color(0xFF0F1F3D);
const kColorCard = Color(0xFF162040);
const kColorBorder = Color(0xFF1E2D50);
const kColorAccent = Color(0xFF00C9A7); // teal
const kColorAccentDim = Color(0xFF007B65);
const kColorWarning = Color(0xFFFFB347);
const kColorDanger = Color(0xFFFF6B6B);
const kColorSuccess = Color(0xFF4ECDC4);
const kColorTextPrimary = Color(0xFFF0F4FF);
const kColorTextSecondary = Color(0xFF8BA3CC);
const kColorTextMuted = Color(0xFF4A6080);

// ── Typography ──────────────────────────────────────────────────────────────
TextStyle kHeadline(BuildContext context) =>
    Theme.of(context).textTheme.headlineSmall!.copyWith(
          color: kColorTextPrimary,
          fontWeight: FontWeight.w700,
          fontFamily: _fontFamily,
        );

TextStyle kTitle(BuildContext context) =>
    Theme.of(context).textTheme.titleMedium!.copyWith(
          color: kColorTextPrimary,
          fontWeight: FontWeight.w600,
          fontFamily: _fontFamily,
        );

TextStyle kBody(BuildContext context) =>
    Theme.of(context).textTheme.bodyMedium!.copyWith(
          color: kColorTextSecondary,
          fontFamily: _fontFamily,
        );

TextStyle kCaption(BuildContext context) =>
    Theme.of(context).textTheme.bodySmall!.copyWith(
          color: kColorTextMuted,
          fontFamily: _fontFamily,
        );

// ── Theme ───────────────────────────────────────────────────────────────────
ThemeData buildAppTheme() => ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      fontFamily: _fontFamily,
      scaffoldBackgroundColor: kColorBackground,
      colorScheme: const ColorScheme.dark(
        primary: kColorAccent,
        secondary: kColorAccentDim,
        surface: kColorSurface,
        error: kColorDanger,
        onPrimary: kColorBackground,
        onSurface: kColorTextPrimary,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: kColorBackground,
        foregroundColor: kColorTextPrimary,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
          fontFamily: _fontFamily,
          fontSize: 18,
          fontWeight: FontWeight.w700,
          color: kColorTextPrimary,
        ),
      ),
      cardTheme: CardThemeData(
        color: kColorCard,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: kColorBorder),
        ),
        margin: EdgeInsets.zero,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: kColorSurface,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: kColorBorder),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: kColorBorder),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: kColorAccent, width: 1.5),
        ),
        labelStyle: const TextStyle(color: kColorTextSecondary),
        hintStyle: const TextStyle(color: kColorTextMuted),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: kColorAccent,
          foregroundColor: kColorBackground,
          minimumSize: const Size.fromHeight(52),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          textStyle: const TextStyle(
            fontFamily: _fontFamily,
            fontWeight: FontWeight.w700,
            fontSize: 16,
          ),
        ),
      ),
      dividerTheme: const DividerThemeData(color: kColorBorder, space: 1),
      listTileTheme: const ListTileThemeData(
        tileColor: kColorCard,
        textColor: kColorTextPrimary,
        subtitleTextStyle: TextStyle(color: kColorTextSecondary),
        iconColor: kColorAccent,
      ),
      chipTheme: ChipThemeData(
        backgroundColor: kColorSurface,
        labelStyle: const TextStyle(color: kColorTextSecondary, fontSize: 12),
        side: const BorderSide(color: kColorBorder),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      ),
      switchTheme: SwitchThemeData(
        thumbColor: WidgetStateProperty.resolveWith(
          (s) => s.contains(WidgetState.selected) ? kColorAccent : kColorTextMuted,
        ),
        trackColor: WidgetStateProperty.resolveWith(
          (s) => s.contains(WidgetState.selected) ? kColorAccentDim : kColorBorder,
        ),
      ),
      snackBarTheme: SnackBarThemeData(
        backgroundColor: kColorCard,
        contentTextStyle: const TextStyle(color: kColorTextPrimary),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        behavior: SnackBarBehavior.floating,
      ),
    );
