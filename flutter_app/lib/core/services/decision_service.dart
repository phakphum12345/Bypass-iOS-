import '../contracts/decision_contract.dart';

class DecisionService {
  const DecisionService();

  DecisionResponse parseAuthoritativeResponse(
    Map<String, dynamic> json,
  ) {
    return DecisionResponse.fromJson(json);
  }
}
