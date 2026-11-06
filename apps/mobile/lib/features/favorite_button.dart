import 'package:flutter/material.dart';
import '../core/favorites.dart';

class FavoriteButton extends StatelessWidget {
  final FavoritesController favorites;
  final String id;
  final bool urdu;
  const FavoriteButton({
    super.key,
    required this.favorites,
    required this.id,
    this.urdu = false,
  });
  @override
  Widget build(BuildContext context) => ListenableBuilder(
    listenable: favorites,
    builder: (context, _) {
      final saved = favorites.ids.contains(id);
      return IconButton(
        tooltip: favorites.failed
            ? (urdu
                  ? 'پسندیدہ محفوظ نہیں ہو سکا۔ دوبارہ آزمائیں'
                  : 'Favorite storage unavailable or full. Retry')
            : (urdu
                  ? (saved ? 'پسندیدہ سے ہٹائیں' : 'پسندیدہ میں شامل کریں')
                  : (saved ? 'Remove favorite' : 'Favorite NGO')),
        isSelected: saved,
        icon: Icon(
          favorites.failed
              ? Icons.error_outline
              : saved
              ? Icons.bookmark
              : Icons.bookmark_border,
        ),
        onPressed: favorites.busy || (!favorites.ready && !favorites.failed)
            ? null
            : () async {
                if (!favorites.ready) {
                  await favorites.load();
                } else {
                  await favorites.setFavorite(id, !saved);
                }
              },
      );
    },
  );
}
