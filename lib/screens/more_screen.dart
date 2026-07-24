import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import '../widgets/common.dart';
import 'library_screen.dart';
import 'figures_screen.dart';
import 'lineage_screen.dart';

/// The "المزيد" tab — a menu that gathers the sections that don't have their
/// own tab (library, figures, lineage) plus app-level actions.
class MoreScreen extends StatelessWidget {
  const MoreScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final items = <_MoreItem>[
      _MoreItem(
        icon: Icons.menu_book_rounded,
        title: 'المكتبة',
        subtitle: 'الصور والوثائق والمخطوطات',
        onTap: () => _push(context, const LibraryScreen()),
      ),
      _MoreItem(
        icon: Icons.workspace_premium_rounded,
        title: 'الشخصيات',
        subtitle: 'شخصيات العائلة البارزة',
        onTap: () => _push(context, const FiguresScreen()),
      ),
      _MoreItem(
        icon: Icons.groups_rounded,
        title: 'النسب',
        subtitle: 'أصل العائلة وجذورها',
        onTap: () => _push(context, const LineageScreen()),
      ),
      _MoreItem(
        icon: Icons.hub_rounded,
        title: 'تواصل ومشاركة',
        subtitle: 'شارك في محتوى التطبيق',
        onTap: () => _showConnect(context),
      ),
      _MoreItem(
        icon: Icons.info_outline_rounded,
        title: 'عن التطبيق',
        subtitle: 'تطبيق أسرة آل ناصر',
        onTap: () => _showAbout(context),
      ),
    ];

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const ScreenHeader(
              title: 'المزيد',
              icon: Icons.grid_view_rounded,
              showHomeButton: false,
            ),
            Expanded(
              child: ListView.separated(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
                itemCount: items.length,
                separatorBuilder: (_, _) => const SizedBox(height: 12),
                itemBuilder: (context, i) => _MoreTile(item: items[i]),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _push(BuildContext context, Widget screen) {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => screen));
  }

  void _showConnect(BuildContext context) {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: AppColors.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(24)),
      ),
      builder: (_) => const _ConnectSheet(),
    );
  }

  void _showAbout(BuildContext context) {
    showDialog<void>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('عن التطبيق', textAlign: TextAlign.right),
        content: const Text(
          'تطبيق أسرة آل ناصر — يجمع أخبار العائلة، مكتبتها، شخصياتها ونسبها في '
          'مكان واحد.',
          textAlign: TextAlign.right,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('حسنًا'),
          ),
        ],
      ),
    );
  }
}

class _MoreItem {
  _MoreItem({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;
}

class _MoreTile extends StatelessWidget {
  const _MoreTile({required this.item});
  final _MoreItem item;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.surface,
      borderRadius: BorderRadius.circular(16),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: item.onTap,
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            boxShadow: AppTheme.cardShadow,
          ),
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
          child: Row(
            children: [
              CircleAvatar(
                radius: 24,
                backgroundColor: AppColors.background,
                child: Icon(item.icon, color: AppColors.primary),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      item.title,
                      style: const TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w700,
                        color: AppColors.primary,
                      ),
                    ),
                    Text(
                      item.subtitle,
                      style: const TextStyle(
                        fontSize: 13,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              const Icon(Icons.chevron_left_rounded,
                  color: AppColors.textSecondary),
            ],
          ),
        ),
      ),
    );
  }
}

class _ConnectSheet extends StatelessWidget {
  const _ConnectSheet();

  @override
  Widget build(BuildContext context) {
    final items = [
      (Icons.person_add_alt_1_rounded, 'إضافة فرد من العائلة'),
      (Icons.photo_camera_back_rounded, 'مشاركة صورة'),
      (Icons.campaign_rounded, 'إرسال خبر'),
      (Icons.support_agent_rounded, 'التواصل مع اللجنة'),
    ];
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 20, 16, 20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'تواصل ومشاركة',
              textAlign: TextAlign.right,
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w700,
                color: AppColors.primary,
              ),
            ),
            const SizedBox(height: 12),
            for (final item in items)
              ListTile(
                trailing: Icon(item.$1, color: AppColors.primary),
                title: Text(item.$2, textAlign: TextAlign.right),
                onTap: () => Navigator.of(context).pop(),
              ),
          ],
        ),
      ),
    );
  }
}
