// Perl Object Example

> object add perl
	my ($rs, @args) = @_;
	return $args[0] + $args[1];
< object

> object md5sum perl
	my ($rs, @args) = @_;
	use Digest::MD5 qw(md5_hex);
	return md5_hex(join(" ", @args));
< object

// Say "add 5 plus 7"
+ add * plus *
- <star1> + <star2> = <call>add <star1> <star2></call>

// Say "hash something in md5"
+ hash * in md5
- MD5 hash: <call>md5sum <star></call>
