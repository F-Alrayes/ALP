import 'package:flutter/material.dart';
import '../data/sample_data.dart';
import '../theme/app_theme.dart';
import '../widgets/app_logo.dart';
import '../widgets/common.dart';

/// Library screen: family documents, photo gallery and manuscripts.
class LibraryScreen extends StatelessWidget {
  const LibraryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const ScreenHeader(title: 'المكتبة', icon: Icons.menu_book_rounded),
            Expanded(
              child: ListView(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
                children: [
                  // Hero: family documents.
                  Container(
                    height: 200,
                    decoration: BoxDecoration(
                      color: const Color(0xFFEDEDE6),
                      borderRadius: BorderRadius.circular(20),
                      boxShadow: AppTheme.cardShadow,
                    ),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: const [
                        Opacity(opacity: 0.35, child: AppLogo(size: 96)),
                        SizedBox(height: 12),
                        Text(
                          'وثائق أسرة آل ريس',
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.w800,
                            color: AppColors.primary,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  // Photo gallery.
                  _LibraryTile(
                    title: 'معرض الصور',
                    icon: Icons.movie_rounded,
                    stats: [
                      _Stat('الألبومات', '${SampleData.totalAlbums}'),
                      _Stat('الصور', '${SampleData.totalPhotos}'),
                    ],
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const _GalleryScreen()),
                    ),
                  ),
                  const SizedBox(height: 18),

                  // Documents & manuscripts.
                  _LibraryTile(
                    title: 'الوثائق و المخطوطات',
                    icon: Icons.description_rounded,
                    stats: [
                      _Stat('العدد', '${SampleData.documents.length}'),
                    ],
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(
                          builder: (_) => const _DocumentsScreen()),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Stat {
  const _Stat(this.label, this.value);
  final String label;
  final String value;
}

class _LibraryTile extends StatelessWidget {
  const _LibraryTile({
    required this.title,
    required this.icon,
    required this.stats,
    this.onTap,
  });

  final String title;
  final IconData icon;
  final List<_Stat> stats;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.surface,
      borderRadius: BorderRadius.circular(20),
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: onTap,
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(20),
            boxShadow: AppTheme.cardShadow,
          ),
          clipBehavior: Clip.antiAlias,
          child: Column(
            children: [
              // Beige banner with the logo watermark + type badge.
              Container(
                height: 130,
                width: double.infinity,
                color: AppColors.beige,
                child: Stack(
                  children: [
                    const Center(child: AppLogo(size: 84)),
                    Positioned(
                      bottom: 12,
                      left: 12,
                      child: CircleAvatar(
                        radius: 22,
                        backgroundColor: AppColors.sage,
                        child: Icon(icon, color: Colors.white),
                      ),
                    ),
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    for (final s in stats) ...[
                      Text('${s.label}  ',
                          style: const TextStyle(
                              color: AppColors.textSecondary)),
                      Text(s.value,
                          style: const TextStyle(
                              fontWeight: FontWeight.w700,
                              color: AppColors.primary)),
                      const SizedBox(width: 20),
                    ],
                    const Spacer(),
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                        color: AppColors.primary,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Grid of albums.
class _GalleryScreen extends StatelessWidget {
  const _GalleryScreen();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const ScreenHeader(title: 'معرض الصور', icon: Icons.movie_rounded),
            Expanded(
              child: GridView.builder(
                padding: const EdgeInsets.all(20),
                gridDelegate:
                    const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  mainAxisSpacing: 16,
                  crossAxisSpacing: 16,
                  childAspectRatio: 0.85,
                ),
                itemCount: SampleData.albums.length,
                itemBuilder: (context, index) {
                  final album = SampleData.albums[index];
                  return Container(
                    decoration: BoxDecoration(
                      color: AppColors.surface,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: AppTheme.cardShadow,
                    ),
                    clipBehavior: Clip.antiAlias,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Expanded(
                          child: Container(
                            color: AppColors.beige,
                            child: const Center(child: AppLogo(size: 56)),
                          ),
                        ),
                        Padding(
                          padding: const EdgeInsets.all(10),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Text(
                                album.title,
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(
                                  fontWeight: FontWeight.w700,
                                  color: AppColors.primary,
                                ),
                              ),
                              Text(
                                '${album.photoCount} صورة',
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: AppColors.textSecondary,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// List of documents & manuscripts.
class _DocumentsScreen extends StatelessWidget {
  const _DocumentsScreen();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const ScreenHeader(
                title: 'الوثائق و المخطوطات',
                icon: Icons.description_rounded),
            Expanded(
              child: ListView.separated(
                padding: const EdgeInsets.all(20),
                itemCount: SampleData.documents.length,
                separatorBuilder: (_, _) => const SizedBox(height: 14),
                itemBuilder: (context, index) {
                  final doc = SampleData.documents[index];
                  return Container(
                    decoration: BoxDecoration(
                      color: AppColors.surface,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: AppTheme.cardShadow,
                    ),
                    child: ListTile(
                      contentPadding: const EdgeInsets.symmetric(
                          horizontal: 18, vertical: 8),
                      trailing: const CircleAvatar(
                        backgroundColor: AppColors.sage,
                        child: Icon(Icons.description_rounded,
                            color: Colors.white),
                      ),
                      title: Text(doc.title, textAlign: TextAlign.right),
                      subtitle: doc.subtitle.isEmpty
                          ? null
                          : Text(doc.subtitle, textAlign: TextAlign.right),
                      onTap: () => showComingSoon(context, 'عرض الوثيقة'),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
