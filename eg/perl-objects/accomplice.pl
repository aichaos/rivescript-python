#!/usr/bin/perl

# The bridge between Python and Perl ;)

use strict;
use warnings;
use RiveScript;
use JSON;

my $json = JSON->new->utf8;

# Read input from Python.
my $input;
while (my $line = <STDIN>) {
	$input .= $line;
}

# JSON-decode it.
my $data;
eval {
	$data = $json->decode($input);
};
if ($@) {
	error("Invalid JSON data!");
}

# Make sure all required fields are there.
foreach my $key (qw(code vars id message)) {
	if (!exists $data->{$key}) {
		error("Required JSON key '$key' doesn't exist!");
	}
}

# Set up RiveScript.
my $rs = RiveScript->new(debug=>0);
my $code = $data->{code};
$rs->stream(qq{
	+ *
	- <call>handle <star></call>

	> object handle perl
		$code
	< object
});
$rs->sortReplies();

# Set all the user vars.
foreach my $var (keys %{$data->{vars}}) {
	$rs->setUservar($data->{id}, $var, $data->{vars}->{$var});
}

# Get the reply.
my $reply = $rs->reply($data->{id}, $data->{message});

# Recover the new user vars.
my $raw = $rs->getUservars($data->{id});
my $vars = {};
foreach my $key (keys %{$raw}) {
	next if ref($raw->{$key});
	$vars->{$key} = $raw->{$key};
}

my $out = {
	status => 'ok',
	reply  => $reply,
	vars   => $vars,
};

print $json->encode($out);
exit(0);

sub error {
	my $mess = shift;
	print $json->encode({
		status  => 'error',
		message => $mess,
	});
	exit(0);
}
