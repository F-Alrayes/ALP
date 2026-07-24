import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../data/sample_data.dart';
import '../models/models.dart';
import '../theme/app_theme.dart';
import '../widgets/common.dart';

/// News / announcements screen with All / Unread tabs, search and
/// date-grouped cards.
class NewsScreen extends StatefulWidget {
  const NewsScreen({super.key});

  @override
  State<NewsScreen> createState() => _NewsScreenState();
}

class _NewsScreenState extends State<NewsScreen> {
  int _tab = 0; // 0 = all, 1 = unread
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final filtered = SampleData.news.where((n) {
      final matchesTab = _tab == 0 || !n.isRead;
      final matchesQuery =
          _query.isEmpty || n.title.contains(_query) || n.body.contains(_query);
      return matchesTab && matchesQuery;
    }).toList();

    final grouped = _groupByDate(filtered);

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const ScreenHeader(title: 'الأخبار', icon: Icons.campaign_rounded),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: SearchField(
                onChanged: (v) => setState(() => _query = v),
              ),
            ),
            const SizedBox(height: 12),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: SegmentTabs(
                labels: const ['جميع الأخبار', 'لم تقرأ'],
                selectedIndex: _tab,
                onChanged: (i) => setState(() => _tab = i),
              ),
            ),
            const SizedBox(height: 8),
            Expanded(
              child: filtered.isEmpty
                  ? const _EmptyState(message: 'لا توجد أخبار')
                  : ListView.builder(
                      padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
                      itemCount: grouped.length,
                      itemBuilder: (context, index) {
                        final entry = grouped[index];
                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            _DateLabel(date: entry.date),
                            for (final item in entry.items)
                              _NewsCard(
                                item: item,
                                onTap: () => _openNews(context, item),
                              ),
                            const SizedBox(height: 16),
                          ],
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }

  void _openNews(BuildContext context, NewsItem item) {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => _NewsDetailScreen(item: item)),
    );
  }

  List<_DateGroup> _groupByDate(List<NewsItem> items) {
    final map = <String, List<NewsItem>>{};
    for (final item in items) {
      final key = DateFormat('yyyy-MM-dd').format(item.date);
      map.putIfAbsent(key, () => []).add(item);
    }
    final groups = map.entries
        .map((e) => _DateGroup(DateTime.parse(e.key), e.value))
        .toList()
      ..sort((a, b) => b.date.compareTo(a.date));
    return groups;
  }
}

class _DateGroup {
  _DateGroup(this.date, this.items);
  final DateTime date;
  final List<NewsItem> items;
}

class _DateLabel extends StatelessWidget {
  const _DateLabel({required this.date});
  final DateTime date;

  static const _weekdays = [
    'الإثنين',
    'الثلاثاء',
    'الأربعاء',
    'الخميس',
    'الجمعة',
    'السبت',
    'الأحد',
  ];

  @override
  Widget build(BuildContext context) {
    final weekday = _weekdays[(date.weekday - 1) % 7];
    final formatted = DateFormat('dd/MM/yyyy').format(date);
    return Padding(
      padding: const EdgeInsets.fromLTRB(0, 8, 4, 8),
      child: Text(
        '$weekday  $formatted',
        textAlign: TextAlign.right,
        style: const TextStyle(
          color: AppColors.textSecondary,
          fontWeight: FontWeight.w600,
          fontSize: 14,
        ),
      ),
    );
  }
}

class _NewsCard extends StatelessWidget {
  const _NewsCard({required this.item, this.onTap});
  final NewsItem item;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Material(
        color: item.isRead ? AppColors.surfaceMuted : AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: onTap,
          child: Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              boxShadow: item.isRead ? null : AppTheme.cardShadow,
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                const Icon(Icons.campaign_rounded,
                    color: AppColors.primary, size: 30),
                const SizedBox(width: 14),
                Expanded(
                  child: Text(
                    item.title,
                    textAlign: TextAlign.right,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: AppColors.primary,
                      height: 1.5,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _NewsDetailScreen extends StatelessWidget {
  const _NewsDetailScreen({required this.item});
  final NewsItem item;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            const ScreenHeader(title: 'الخبر', icon: Icons.campaign_rounded),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Icon(Icons.campaign_rounded,
                        color: AppColors.primary, size: 48),
                    const SizedBox(height: 16),
                    Text(
                      item.title,
                      textAlign: TextAlign.center,
                      style: const TextStyle(
                        fontSize: 22,
                        fontWeight: FontWeight.w700,
                        color: AppColors.primary,
                        height: 1.6,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      DateFormat('dd/MM/yyyy').format(item.date),
                      textAlign: TextAlign.center,
                      style: const TextStyle(color: AppColors.textSecondary),
                    ),
                    const SizedBox(height: 24),
                    Text(
                      item.body,
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

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.message});
  final String message;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.inbox_rounded,
              size: 56, color: AppColors.textSecondary),
          const SizedBox(height: 12),
          Text(message,
              style: const TextStyle(color: AppColors.textSecondary)),
        ],
      ),
    );
  }
}
