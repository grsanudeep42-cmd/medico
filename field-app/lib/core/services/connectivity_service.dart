import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:flutter/foundation.dart';

/// Wraps `connectivity_plus` and exposes a [ValueNotifier<bool>] that is
/// `true` when any usable network interface is available.
class ConnectivityService extends ChangeNotifier {
  ConnectivityService() {
    _init();
  }

  bool _isOnline = false;
  bool get isOnline => _isOnline;

  late final Stream<List<ConnectivityResult>> _stream;

  Future<void> _init() async {
    final connectivity = Connectivity();

    // Check current state immediately
    final initial = await connectivity.checkConnectivity();
    _isOnline = _hasConnection(initial);
    notifyListeners();

    // Subscribe to changes
    _stream = connectivity.onConnectivityChanged;
    _stream.listen((results) {
      final online = _hasConnection(results);
      if (online != _isOnline) {
        _isOnline = online;
        notifyListeners();
      }
    });
  }

  bool _hasConnection(List<ConnectivityResult> results) =>
      results.any((r) =>
          r == ConnectivityResult.mobile ||
          r == ConnectivityResult.wifi ||
          r == ConnectivityResult.ethernet ||
          r == ConnectivityResult.vpn);
}
