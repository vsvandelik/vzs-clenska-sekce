***************************************
Synchronizace plateb s bankou
***************************************

Jednou z vlastností systému je synchronizace plateb s FIO bankou. Pokud je systém správně
nastaven administrátorem, synchronizace probíhá pravidelně podle nastavení, například každý den
nebo každou hodinu a ověřuje, zda přijaté platby, které jsou ve výpisu z účtu,
odpovídají některé z plateb v systému. Pokud ano, tak se platba v systému označí jako zaplacená.

Transakce se párují na základě variabilního symbolu. V případě nalezení platby se stejným
variabilním symbolem, ale s odlišnou částkou, platba se neoznačí jako zaplacená a
správce transakcí obdrží e-mailové upozornění o této odlišnosti.

Správce obdrží upozornění i v případě, kdy se na účtu objeví platba s duplicitním variabilním
symbolem ve srovnání s platbou, která již byla spárovaná.