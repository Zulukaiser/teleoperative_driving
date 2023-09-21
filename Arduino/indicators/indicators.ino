#define indicator_l_sens 6
#define indicator_r_sens 7
#define indicator_l_act 8
#define indicator_r_act 9

void setup() {
  // put your setup code here, to run once:
  pinMode(indicator_l_sens, INPUT);
  pinMode(indicator_r_sens, INPUT);
  pinMode(indicator_l_act, OUTPUT);
  pinMode(indicator_r_act, OUTPUT);
}

void loop() {
  // put your main code here, to run repeatedly:
  int l = digitalRead(indicator_l_sens);
  int r = digitalRead(indicator_r_sens);

  if (l == 1) {
    digitalWrite(indicator_l_act, HIGH);
  }
  if (r == 1) {
    digitalWrite(indicator_r_act, HIGH);
  }
  delay(500);
  digitalWrite(indicator_l_act, LOW);
  digitalWrite(indicator_r_act, LOW);
  delay(500);
}
