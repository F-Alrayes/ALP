import 'package:flutter/material.dart';
import '../data/sample_data.dart';
import '../models/models.dart';
import '../widgets/common.dart';
import '../widgets/feed.dart';

/// News / announcements screen with All / Unread tabs, search and
/// date-grouped cards.
class NewsScreen extends StatefulWidget {
  const NewsScreen({super.key, this.showHomeButton = false});

  /// True when pushed (e.g. from a home card); false when shown as a tab.
  final bool showHomeButton;

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

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            ScreenHeader(
              title: 'الأخبار',
              icon: Icons.campaign_rounded,
              showHomeButton: widget.showHomeButton,
            ),
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
              child: FeedListView(
                items: filtered,
                icon: Icons.campaign_rounded,
                emptyMessage: 'لا توجد أخبار',
                onOpen: (item) => _openNews(context, item),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _openNews(BuildContext context, NewsItem item) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => AnnouncementDetailScreen(
          item: item,
          headerTitle: 'الخبر',
          icon: Icons.campaign_rounded,
        ),
      ),
    );
  }
}
