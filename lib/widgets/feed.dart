import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/models.dart';
import '../theme/app_theme.dart';
import 'common.dart';

/// A reusable, date-grouped list of announcement-style items (news, marriages,
/// condolences, occasions …). Screens supply the filtered [items] and an
/// [onOpen] callback; the section [icon] is used on each card.
class FeedListView extends StatelessWidget {
  const FeedListView({
    super.key,
    required this.items,
    required this.onOpen,
    this.icon = Icons.campaign_rounded,
    this.emptyMessage = 'لا يوجد محتوى',
    this.padding = const EdgeInsets.fromLTRB(20, 8, 20, 24),
  });

  final List<NewsItem> items;
  final void Function(NewsItem) onOpen;
  final IconData icon;
  final String emptyMessage;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) {
    if (items.isEmpty) return FeedEmptyState(message: emptyMessage);
    final grouped = _groupByDate(items);
    return ListView.builder(
      padding: padding,
      itemCount: grouped.length,
      itemBuilder: (context, index) {
        final entry = grouped[index];
        return Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            _DateLabel(date: entry.date),
            for (final item in entry.items)
              _FeedCard(item: item, icon: icon, onTap: () => onOpen(item)),
            const SizedBox(height: 16),
          ],
        );
      },
    );
  }

  List<_DateGroup> _groupByDate(List<NewsItem> items) {
    final map = <String, List<NewsItem>>{};
    for (final item in items) {
      final key = DateFormat('yyyy-MM-dd').format(item.date);
      map.putIfAbsent(key, () => []).add(item);
    }
    return map.entries
        .map((e) => _DateGroup(DateTime.parse(e.key), e.value))
        .toList()
      ..sort((a, b) => b.date.compareTo(a.date));
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

class _FeedCard extends StatelessWidget {
  const _FeedCard({required this.item, required this.icon, this.onTap});
  final NewsItem item;
  final IconData icon;
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
                Icon(icon, color: AppColors.primary, size: 30),
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

/// Detail view for a single announcement item.
class AnnouncementDetailScreen extends StatelessWidget {
  const AnnouncementDetailScreen({
    super.key,
    required this.item,
    required this.headerTitle,
    this.icon = Icons.campaign_rounded,
  });

  final NewsItem item;
  final String headerTitle;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            ScreenHeader(title: headerTitle, icon: icon),
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Icon(icon, color: AppColors.primary, size: 48),
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

class FeedEmptyState extends StatelessWidget {
  const FeedEmptyState({super.key, required this.message});
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
