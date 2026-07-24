import '../models/models.dart';

/// Local sample data used for the first version of the app.
///
/// Replace these with a backend / repository layer when the API is ready — the
/// screens only depend on the model types, not on where the data comes from.
class SampleData {
  SampleData._();

  static final List<NewsItem> news = [
    NewsItem(
      id: 'n1',
      title: 'صور ومقطع إجتماع عيد الاضحى لعام 1447/2026',
      date: DateTime(2026, 6, 29),
      body:
          'يسر اللجنة أن تشارككم صور ومقطع فيديو من اجتماع العائلة بمناسبة عيد '
          'الأضحى المبارك لهذا العام. نسأل الله أن يعيده على الجميع باليمن '
          'والبركات.',
    ),
    NewsItem(
      id: 'n2',
      title: 'عيد أضحى مبارك',
      date: DateTime(2026, 5, 26),
      body: 'كل عام وأسرة آل ناصر بخير بمناسبة عيد الأضحى المبارك.',
    ),
    NewsItem(
      id: 'n3',
      title:
          'دعوة عيد الأضحى المبارك 1447 آل ناصر (رجال) قاعة هوليدي ان القصر حي '
          'العليا حياكم الله',
      date: DateTime(2026, 5, 25),
      body:
          'تتشرف اللجنة بدعوتكم لحضور حفل العيد السنوي للرجال في قاعة هوليدي إن '
          'القصر بحي العليا. الحضور من بعد صلاة العشاء.',
    ),
    NewsItem(
      id: 'n4',
      title: 'دعوة عيد الاضحى المبارك',
      date: DateTime(2026, 5, 25),
      body: 'يسعدنا حضوركم ومشاركتكم فرحة العيد مع العائلة.',
    ),
    NewsItem(
      id: 'n5',
      title:
          'سعد بن عبدالله بن عبدالرحمن العجلان إلى رحمة الله … إنا لله وإنا إليه '
          'راجعون',
      date: DateTime(2026, 5, 5),
      body:
          'انتقل إلى رحمة الله تعالى الفقيد سعد بن عبدالله. نسأل الله أن يتغمده '
          'بواسع رحمته ويسكنه فسيح جناته.',
      isRead: true,
    ),
  ];

  static final List<Figure> figures = [
    Figure(
      id: 'f1',
      firstName: 'سليمان',
      fullName: 'حمد سليمان محمد',
      isPinned: true,
    ),
    Figure(
      id: 'f2',
      firstName: 'محمد',
      fullName: 'عبدالرحمن عبدالله سليمان',
      isPinned: true,
    ),
    Figure(
      id: 'f3',
      firstName: 'علي',
      fullName: 'عبدالعزيز علي محمد',
      isPinned: true,
    ),
    Figure(
      id: 'f4',
      firstName: 'عبدالله',
      fullName: 'محمد علي محمد',
      isPinned: true,
    ),
    Figure(
      id: 'f5',
      firstName: 'عبدالله',
      fullName: 'علي محمد عثمان',
      isPinned: true,
    ),
    Figure(
      id: 'f6',
      firstName: 'سليمان',
      fullName: 'عبدالعزيز عبدالله عثمان',
      isPinned: true,
    ),
    Figure(
      id: 'f7',
      firstName: 'إبراهيم',
      fullName: 'عبدالله إبراهيم محمد',
    ),
    Figure(
      id: 'f8',
      firstName: 'خالد',
      fullName: 'سعد عبدالرحمن سليمان',
    ),
  ];

  static const List<Album> albums = [
    Album(id: 'a1', title: 'اجتماع عيد الأضحى 1447', photoCount: 320),
    Album(id: 'a2', title: 'اللقاء السنوي', photoCount: 210),
    Album(id: 'a3', title: 'صور تاريخية', photoCount: 145),
    Album(id: 'a4', title: 'مناسبات العائلة', photoCount: 480),
  ];

  static const int totalPhotos = 2156;
  static const int totalAlbums = 11;

  static const List<LibraryDocument> documents = [
    LibraryDocument(
      id: 'd1',
      title: 'مخطوطة نسب أسرة آل ناصر',
      subtitle: 'وثيقة تاريخية',
    ),
    LibraryDocument(
      id: 'd2',
      title: 'وثيقة ملكية قديمة',
      subtitle: 'أرشيف العائلة',
    ),
  ];

  /// The lineage text shown on the النسب screen.
  static const String lineageTitle = 'نسب العائلة';

  // Placeholder narrative for آل ناصر — replace with the family's official
  // history and references when available.
  static const String lineageBody =
      'أسرة آل ناصر من الأسر المعروفة، ويجمع هذا القسم نبذة عن أصولها وجذورها '
      'التاريخية وأبرز محطاتها. هذا نص تمهيدي يمكن تحديثه لاحقًا بالمحتوى '
      'الرسمي المعتمد من العائلة.';

  static const String lineageQuote = '';

  static const String lineageReferenceTitle = 'المراجع والمصادر';
  static const String lineageReference = 'قيد الإعداد';
}
