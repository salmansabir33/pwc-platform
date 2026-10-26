// Requires a real Android/iOS runner. This is native storage/lifecycle
// integration with a synthetic API, NOT live backend or delivery acceptance.
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:pwc_mobile/core/storage.dart';
import 'package:pwc_mobile/core/session_controller.dart';
import '../test/fakes.dart';
void main(){
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets('native vault restores only via rotation and erases on logout',(tester)async{
    final vault=NativeCredentialStore();await vault.clear();
    final first=SessionController(FakeApi(),vault,clock:()=>DateTime.utc(2026,10,26));
    await first.login('person@example.invalid','synthetic-password');
    expect(first.authenticated,true);first.dispose();
    final next=SessionController(FakeApi(),vault,clock:()=>DateTime.utc(2026,10,26));
    try{
      await next.restore();expect(next.authenticated,true);
      await next.logout();expect(await vault.read(),null);expect(next.authenticated,false);
    }finally{next.dispose();await vault.clear();}
  });
}
