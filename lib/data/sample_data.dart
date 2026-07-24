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

  /// Marriage announcements (زواجات).
  static final List<NewsItem> marriages = [
    NewsItem(
      id: 'm1',
      title: 'زواج الشاب عبدالله بن محمد آل ناصر',
      date: DateTime(2026, 7, 12),
      body:
          'تتقدم أسرة آل ناصر بأصدق التهاني والتبريكات بمناسبة زواج ابنها '
          'عبدالله، سائلين الله أن يتمم لهما على خير وأن يبارك لهما ويجمع بينهما '
          'في خير.',
    ),
    NewsItem(
      id: 'm2',
      title: 'حفل زفاف سعد بن إبراهيم آل ناصر',
      date: DateTime(2026, 6, 20),
      body:
          'يسر العائلة دعوتكم لحضور حفل الزفاف يوم الجمعة بعد صلاة العشاء في قاعة '
          'المناسبات. بحضوركم تكتمل الفرحة.',
    ),
    NewsItem(
      id: 'm3',
      title: 'ملكة الشاب فيصل بن عبدالعزيز',
      date: DateTime(2026, 5, 3),
      body: 'مبارك للعروسين، نسأل الله لهما التوفيق ودوام السعادة.',
      isRead: true,
    ),
  ];

  /// Condolences (تعازي).
  static final List<NewsItem> condolences = [
    NewsItem(
      id: 'c1',
      title: 'وفاة المغفور له بإذن الله عبدالرحمن بن سليمان … إنا لله وإنا '
          'إليه راجعون',
      date: DateTime(2026, 7, 8),
      body:
          'انتقل إلى رحمة الله تعالى، تقبل العزاء في مقبرة الأسرة بعد صلاة '
          'العصر. نسأل الله أن يتغمده بواسع رحمته ويسكنه فسيح جناته.',
    ),
    NewsItem(
      id: 'c2',
      title: 'تعزية في وفاة الحاجة أم عبدالله … رحمها الله',
      date: DateTime(2026, 6, 2),
      body:
          'ببالغ الحزن والأسى ننعى إليكم فقيدتنا، سائلين المولى أن يرحمها '
          'ويلهم أهلها الصبر والسلوان.',
      isRead: true,
    ),
  ];

  /// Occasions & celebrations (مناسبات) — newborns, graduations, achievements.
  static final List<NewsItem> occasions = [
    NewsItem(
      id: 'o1',
      title: 'مولود جديد في العائلة — مبارك المقدم',
      date: DateTime(2026, 7, 18),
      body:
          'رزق الأستاذ محمد بمولوده الجديد، بارك الله له في الموهوب وجعله من '
          'الذرية الصالحة.',
    ),
    NewsItem(
      id: 'o2',
      title: 'تخرّج المهندس خالد بن سعد من جامعة الملك سعود',
      date: DateTime(2026, 6, 28),
      body:
          'ألف مبروك التخرج، ونسأل الله له التوفيق والسداد في حياته العملية.',
    ),
    NewsItem(
      id: 'o3',
      title: 'تكريم أحد أبناء العائلة على تفوقه الدراسي',
      date: DateTime(2026, 5, 15),
      body: 'نفخر بتفوق أبنائنا ونسأل الله لهم دوام التميز.',
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
