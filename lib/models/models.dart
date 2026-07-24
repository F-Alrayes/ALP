/// Simple immutable data models for the app.
///
/// For this first version the data is served from local sample data
/// (see `data/sample_data.dart`). These models are intentionally plain so they
/// can later be populated from a backend / JSON without changing the UI.
library;

/// A news / announcement item shown on the News screen and Home preview.
class NewsItem {
  const NewsItem({
    required this.id,
    required this.title,
    required this.date,
    this.body = '',
    this.isRead = false,
  });

  final String id;
  final String title;
  final DateTime date;
  final String body;
  final bool isRead;

  NewsItem copyWith({bool? isRead}) => NewsItem(
        id: id,
        title: title,
        date: date,
        body: body,
        isRead: isRead ?? this.isRead,
      );
}

/// A notable family figure (شخصية).
class Figure {
  const Figure({
    required this.id,
    required this.firstName,
    required this.fullName,
    this.imageUrl,
    this.isPinned = false,
    this.bio = '',
  });

  final String id;
  final String firstName;
  final String fullName;

  /// Optional remote/asset image. When null a placeholder avatar is shown.
  final String? imageUrl;
  final bool isPinned;
  final String bio;
}

/// A photo album in the library gallery.
class Album {
  const Album({
    required this.id,
    required this.title,
    required this.photoCount,
    this.coverAsset,
  });

  final String id;
  final String title;
  final int photoCount;
  final String? coverAsset;
}

/// A document or manuscript in the library.
class LibraryDocument {
  const LibraryDocument({
    required this.id,
    required this.title,
    this.subtitle = '',
  });

  final String id;
  final String title;
  final String subtitle;
}
