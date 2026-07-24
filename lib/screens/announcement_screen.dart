import 'package:flutter/material.dart';
import '../models/models.dart';
import '../widgets/common.dart';
import '../widgets/feed.dart';

/// A generic section that shows a searchable, date-grouped list of
/// announcement items — used for زواجات / تعازي / مناسبات.
class AnnouncementScreen extends StatefulWidget {
  const AnnouncementScreen({
    super.key,
    required this.title,
    required this.icon,
    required this.items,
    required this.detailTitle,
    this.emptyMessage = 'لا يوجد محتوى',
    this.showHomeButton = false,
  });

  final String title;
  final IconData icon;
  final List<NewsItem> items;

  /// Header shown on an item's detail page (e.g. "تعزية").
  final String detailTitle;
  final String emptyMessage;

  /// Whether to show the home button (true when pushed, false inside a tab).
  final bool showHomeButton;

  @override
  State<AnnouncementScreen> createState() => _AnnouncementScreenState();
}

class _AnnouncementScreenState extends State<AnnouncementScreen> {
  String _query = '';

  @override
  Widget build(BuildContext context) {
    final filtered = widget.items.where((n) {
      return _query.isEmpty ||
          n.title.contains(_query) ||
          n.body.contains(_query);
    }).toList();

    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            ScreenHeader(
              title: widget.title,
              icon: widget.icon,
              showHomeButton: widget.showHomeButton,
            ),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: SearchField(
                onChanged: (v) => setState(() => _query = v),
              ),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: FeedListView(
                items: filtered,
                icon: widget.icon,
                emptyMessage: widget.emptyMessage,
                onOpen: (item) => Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => AnnouncementDetailScreen(
                      item: item,
                      headerTitle: widget.detailTitle,
                      icon: widget.icon,
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
