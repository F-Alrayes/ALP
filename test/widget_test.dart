import 'package:flutter_test/flutter_test.dart';

import 'package:alp/main.dart';

void main() {
  testWidgets('App renders home screen sections', (WidgetTester tester) async {
    await tester.pumpWidget(const AlRayesApp());
    await tester.pump();

    // Core home sections should be present.
    expect(find.text('الأخبار'), findsOneWidget);
    expect(find.text('المكتبة'), findsOneWidget);
    expect(find.text('النسب'), findsOneWidget);
    expect(find.text('الشخصيات'), findsOneWidget);
    expect(find.text('دخول'), findsOneWidget);
  });
}
