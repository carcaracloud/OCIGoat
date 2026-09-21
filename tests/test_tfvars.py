from ocigoat.tfvars import build_var_args, discover_declared_variables


def test_discover_variables_iam_001(real_repo_root):
    terraform_dir = real_repo_root / "scenarios" / "SCN-IAM-001" / "terraform"
    declared = discover_declared_variables(terraform_dir)
    assert declared == {"tenancy_ocid", "test_user_email", "test_user_api_public_key"}


def test_discover_variables_net_001(real_repo_root):
    terraform_dir = real_repo_root / "scenarios" / "SCN-NET-001" / "terraform"
    declared = discover_declared_variables(terraform_dir)
    assert declared == {
        "compartment_id",
        "instance_shape",
        "instance_ocpus",
        "instance_memory_in_gbs",
        "availability_domain_name",
        "test_service_port",
        "operator_ssh_public_key",
    }


def test_discover_variables_database_001(real_repo_root):
    terraform_dir = real_repo_root / "scenarios" / "SCN-DATABASE-001" / "terraform"
    declared = discover_declared_variables(terraform_dir)
    assert declared == {"compartment_id", "admin_password"}


def test_build_var_args_only_includes_declared_and_known():
    declared = {"compartment_id", "admin_password"}
    known_values = {"compartment_id": "ocid1.compartment.oc1..abc", "tenancy_ocid": "ocid1.tenancy.oc1..xyz"}
    args = build_var_args(declared, known_values)
    assert args == ["-var=compartment_id=ocid1.compartment.oc1..abc"]


def test_build_var_args_uses_extra_vars_for_undeclared_unknowns():
    declared = {"compartment_id", "admin_password"}
    known_values = {"compartment_id": "ocid1.compartment.oc1..abc"}
    args = build_var_args(declared, known_values, extra_vars={"admin_password": "s3cret!"})
    assert set(args) == {"-var=compartment_id=ocid1.compartment.oc1..abc", "-var=admin_password=s3cret!"}


def test_build_var_args_never_includes_undeclared_names():
    declared = {"compartment_id"}
    known_values = {"compartment_id": "ocid1.compartment.oc1..abc", "tenancy_ocid": "ocid1.tenancy.oc1..xyz"}
    args = build_var_args(declared, known_values)
    assert args == ["-var=compartment_id=ocid1.compartment.oc1..abc"]
