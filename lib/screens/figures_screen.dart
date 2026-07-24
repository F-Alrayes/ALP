import 'package:flutter/material.dart';
import '../data/sample_data.dart';
import '../models/models.dart';
import '../theme/app_theme.dart';
import '../widgets/common.dart';

/// Notable family figures, with Pinned / Alphabetical tabs, search and a grid.
class FiguresScreen extends StatefulWidget {
  const FiguresScreen({super.key});

  @override
  State<FiguresScreen> createState() => _FiguresScreenState();
}

class _FiguresScreenState extends State<FiguresScreen> {
  int _tab = 0; // 0 = pinned, 1 = alphabetical
  String _query = '';

  @override
  Widget build(BuildContext context) {
    var list = SampleData.figures.where((f) {
      if (_query.isEmpty) return true;
      return f.firstName.contains(_query) || f.fullName.contains(_query);
    }).toList();

    if (_tab == 0) {
      list = list.where((f) => f.isPinned).toList();
    } else {
      list = [...list]..sort((a, b) => a.firstName.compareTo(b.firstName));
    }

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const ScreenHeader(
                title: 'شخصيات', icon: Icons.workspace_premium_rounded),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: SearchField(
                hintText: 'إبحث',
                onChanged: (v) => setState(() => _query = v),
              ),
            ),
            const SizedBox(height: 12),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: SegmentTabs(
                labels: const ['شخصيات مثبتة', 'الأحرف مرتبة أبجديًا'],
                selectedIndex: _tab,
                onChanged: (i) => setState(() => _tab = i),
              ),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: list.isEmpty
                  ? const Center(
                      child: Text('لا توجد نتائج',
                          style: TextStyle(color: AppColors.textSecondary)),
                    )
                  : GridView.builder(
                      padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
                      gridDelegate:
                          const SliverGridDelegateWithFixedCrossAxisCount(
                        crossAxisCount: 2,
                        mainAxisSpacing: 16,
                        crossAxisSpacing: 16,
                        childAspectRatio: 0.78,
                      ),
                      itemCount: list.length,
                      itemBuilder: (context, index) => _FigureCard(
                        figure: list[index],
                        onTap: () => _openFigure(context, list[index]),
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }

  void _openFigure(BuildContext context, Figure figure) {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => _FigureDetailScreen(figure: figure)),
    );
  }
}

class _FigureCard extends StatelessWidget {
  const _FigureCard({required this.figure, this.onTap});
  final Figure figure;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppColors.surface,
      borderRadius: BorderRadius.circular(18),
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: onTap,
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(18),
            boxShadow: AppTheme.cardShadow,
          ),
          padding: const EdgeInsets.all(14),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const PlaceholderAvatar(radius: 44),
              const SizedBox(height: 14),
              Text(
                figure.firstName,
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.w800,
                  color: AppColors.primary,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                figure.fullName,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  fontSize: 13,
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FigureDetailScreen extends StatelessWidget {
  const _FigureDetailScreen({required this.figure});
  final Figure figure;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const ScreenHeader(
                title: 'شخصية', icon: Icons.workspace_premium_rounded),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    const PlaceholderAvatar(radius: 64),
                    const SizedBox(height: 16),
                    Text(
                      figure.firstName,
                      style: const TextStyle(
                        fontSize: 26,
                        fontWeight: FontWeight.w800,
                        color: AppColors.primary,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      figure.fullName,
                      style: const TextStyle(
                        fontSize: 16,
                        color: AppColors.textSecondary,
                      ),
                    ),
                    const SizedBox(height: 24),
                    Text(
                      figure.bio.isEmpty
                          ? 'لا تتوفر نبذة تفصيلية عن هذه الشخصية بعد.'
                          : figure.bio,
                      textAlign: TextAlign.right,
                      style: const TextStyle(fontSize: 16, height: 1.9),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
